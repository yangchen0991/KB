"""
内置工作流节点
提供常用的工作流节点实现
"""

import json
import subprocess
import time
from datetime import datetime, timedelta
from typing import Any, Dict

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db import connection

from .base import ActionNode, BaseNode, ConditionalNode, DataProcessingNode


class StartNode(BaseNode):
    """开始节点"""

    def _define_inputs(self) -> Dict[str, Dict[str, Any]]:
        return {}

    def _define_outputs(self) -> Dict[str, Dict[str, Any]]:
        return {"workflow_data": {"type": "dict", "description": "工作流输入数据"}}

    def execute(self, input_data: Dict[str, Any], context) -> Dict[str, Any]:
        self.log_info("工作流开始执行")
        return {"workflow_data": context.input_data}


class EndNode(BaseNode):
    """结束节点"""

    def _define_inputs(self) -> Dict[str, Dict[str, Any]]:
        return {
            "result": {
                "type": "any",
                "description": "工作流执行结果",
                "required": False,
            }
        }

    def _define_outputs(self) -> Dict[str, Dict[str, Any]]:
        return {}

    def execute(self, input_data: Dict[str, Any], context) -> Dict[str, Any]:
        result = input_data.get("result", {})
        context.output_data = result
        self.log_info("工作流执行结束")
        return {}


class ConditionNode(ConditionalNode):
    """条件判断节点"""

    CONFIG_SCHEMA = {
        "condition_expression": {
            "type": "string",
            "description": "条件表达式",
            "required": True,
        }
    }

    def _define_inputs(self) -> Dict[str, Dict[str, Any]]:
        return {
            "data": {
                "type": "any",
                "description": "用于条件判断的数据",
                "required": True,
            }
        }

    def evaluate_condition(self, input_data: Dict[str, Any], context) -> bool:
        expression = self.get_config_value("condition_expression", "True")
        data = input_data.get("data")

        try:
            # 简单的条件表达式评估
            # 支持基本的比较操作
            if isinstance(data, dict):
                # 将数据注入到局部变量中
                local_vars = data.copy()
                local_vars["data"] = data
                result = eval(expression, {"__builtins__": {}}, local_vars)
            else:
                result = eval(expression, {"__builtins__": {}}, {"data": data})

            return bool(result)
        except Exception as e:
            self.log_error(f"条件表达式评估失败: {str(e)}")
            return False


class ScriptNode(ActionNode):
    """脚本执行节点"""

    CONFIG_SCHEMA = {
        "script_type": {
            "type": "string",
            "enum": ["python", "shell", "javascript"],
            "default": "python",
            "description": "脚本类型",
        },
        "script_content": {
            "type": "string",
            "description": "脚本内容",
            "required": True,
        },
    }

    def _define_inputs(self) -> Dict[str, Dict[str, Any]]:
        return {
            "input_data": {
                "type": "any",
                "description": "脚本输入数据",
                "required": False,
            }
        }

    def _define_outputs(self) -> Dict[str, Dict[str, Any]]:
        return {
            "output_data": {"type": "any", "description": "脚本输出数据"},
            "exit_code": {"type": "number", "description": "退出码"},
        }

    def perform_action(self, input_data: Dict[str, Any], context) -> Dict[str, Any]:
        script_type = self.get_config_value("script_type", "python")
        script_content = self.get_config_value("script_content", "")

        if script_type == "python":
            return self._execute_python_script(script_content, input_data, context)
        elif script_type == "shell":
            return self._execute_shell_script(script_content, input_data)
        else:
            raise ValueError(f"不支持的脚本类型: {script_type}")

    def _execute_python_script(
        self, script: str, input_data: Dict[str, Any], context
    ) -> Dict[str, Any]:
        """执行Python脚本"""
        try:
            # 准备执行环境
            local_vars = {
                "input_data": input_data.get("input_data"),
                "context": context,
                "output_data": None,
            }

            # 执行脚本
            exec(script, {"__builtins__": {}}, local_vars)

            return {"output_data": local_vars.get("output_data"), "exit_code": 0}
        except Exception as e:
            self.log_error(f"Python脚本执行失败: {str(e)}")
            return {"output_data": None, "exit_code": 1, "error": str(e)}

    def _execute_shell_script(
        self, script: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行Shell脚本"""
        try:
            # 将输入数据作为环境变量传递
            env = {}
            if input_data.get("input_data"):
                env["INPUT_DATA"] = json.dumps(input_data["input_data"])

            # 安全性改进：验证脚本内容，防止命令注入
            if not self._validate_script_safety(script):
                raise ValueError("脚本包含不安全的命令")

            # 执行脚本
            result = subprocess.run(
                script,
                shell=True,  # 保持shell=True以支持复杂脚本
                capture_output=True,
                text=True,
                env=env,
                timeout=300,  # 5分钟超时
            )

            return {
                "output_data": result.stdout,
                "exit_code": result.returncode,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {"output_data": None, "exit_code": -1, "error": "脚本执行超时"}
        except Exception as e:
            return {"output_data": None, "exit_code": -1, "error": str(e)}

    def _validate_script_safety(self, script: str) -> bool:
        """验证脚本安全性，防止恶意命令执行"""
        # 危险命令黑名单
        dangerous_commands = [
            'rm -rf', 'del /f', 'format', 'fdisk', 'mkfs',
            'dd if=', 'shutdown', 'reboot', 'halt',
            'passwd', 'su ', 'sudo ', 'chmod 777',
            'wget http', 'curl http', 'nc ', 'netcat',
            '>/dev/', 'cat /etc/passwd', 'cat /etc/shadow',
            'eval(', 'exec(', '__import__',
        ]

        # 检查是否包含危险命令
        script_lower = script.lower()
        for dangerous_cmd in dangerous_commands:
            if dangerous_cmd in script_lower:
                self.log_error(f"脚本包含危险命令: {dangerous_cmd}")
                return False

        # 检查脚本长度（防止过长的恶意脚本）
        if len(script) > 10000:  # 10KB限制
            self.log_error("脚本内容过长")
            return False

        return True


class HttpRequestNode(ActionNode):
    """HTTP请求节点"""

    CONFIG_SCHEMA = {
        "method": {
            "type": "string",
            "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
            "default": "GET",
            "description": "HTTP方法",
        },
        "url": {"type": "string", "description": "请求URL", "required": True},
        "headers": {"type": "dict", "description": "请求头", "default": {}},
        "timeout": {"type": "number", "default": 30, "description": "超时时间（秒）"},
    }

    def _define_inputs(self) -> Dict[str, Dict[str, Any]]:
        return {
            "data": {"type": "any", "description": "请求数据", "required": False},
            "params": {"type": "dict", "description": "URL参数", "required": False},
        }

    def _define_outputs(self) -> Dict[str, Dict[str, Any]]:
        return {
            "response_data": {"type": "any", "description": "响应数据"},
            "status_code": {"type": "number", "description": "HTTP状态码"},
            "headers": {"type": "dict", "description": "响应头"},
        }

    def perform_action(self, input_data: Dict[str, Any], context) -> Dict[str, Any]:
        method = self.get_config_value("method", "GET")
        url = self.get_config_value("url")
        headers = self.get_config_value("headers", {})
        timeout = self.get_config_value("timeout", 30)

        try:
            # 准备请求参数
            kwargs = {"timeout": timeout, "headers": headers}

            if input_data.get("params"):
                kwargs["params"] = input_data["params"]

            if input_data.get("data") and method in ["POST", "PUT", "PATCH"]:
                if isinstance(input_data["data"], dict):
                    kwargs["json"] = input_data["data"]
                else:
                    kwargs["data"] = input_data["data"]

            # 发送请求
            response = requests.request(method, url, **kwargs)

            # 解析响应
            try:
                response_data = response.json()
            except:
                response_data = response.text

            return {
                "response_data": response_data,
                "status_code": response.status_code,
                "headers": dict(response.headers),
            }

        except requests.RequestException as e:
            self.log_error(f"HTTP请求失败: {str(e)}")
            return {
                "response_data": None,
                "status_code": 0,
                "headers": {},
                "error": str(e),
            }


class EmailNode(ActionNode):
    """邮件发送节点"""

    CONFIG_SCHEMA = {
        "subject": {"type": "string", "description": "邮件主题", "required": True},
        "from_email": {"type": "string", "description": "发件人邮箱"},
    }

    def _define_inputs(self) -> Dict[str, Dict[str, Any]]:
        return {
            "to_emails": {
                "type": "list",
                "description": "收件人邮箱列表",
                "required": True,
            },
            "message": {"type": "string", "description": "邮件内容", "required": True},
        }

    def _define_outputs(self) -> Dict[str, Dict[str, Any]]:
        return {
            "success": {"type": "boolean", "description": "发送是否成功"},
            "message_count": {"type": "number", "description": "发送的邮件数量"},
        }

    def perform_action(self, input_data: Dict[str, Any], context) -> Dict[str, Any]:
        subject = self.get_config_value("subject")
        from_email = self.get_config_value("from_email", settings.DEFAULT_FROM_EMAIL)
        to_emails = input_data.get("to_emails", [])
        message = input_data.get("message", "")

        try:
            count = send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=to_emails,
                fail_silently=False,
            )

            return {"success": True, "message_count": count}

        except Exception as e:
            self.log_error(f"邮件发送失败: {str(e)}")
            return {"success": False, "message_count": 0, "error": str(e)}


class DelayNode(ActionNode):
    """延迟节点"""

    CONFIG_SCHEMA = {
        "delay_seconds": {
            "type": "number",
            "default": 1,
            "description": "延迟时间（秒）",
        }
    }

    def _define_inputs(self) -> Dict[str, Dict[str, Any]]:
        return {}

    def _define_outputs(self) -> Dict[str, Dict[str, Any]]:
        return {"delayed_time": {"type": "number", "description": "实际延迟时间"}}

    def perform_action(self, input_data: Dict[str, Any], context) -> Dict[str, Any]:
        delay_seconds = self.get_config_value("delay_seconds", 1)

        self.log_info(f"延迟 {delay_seconds} 秒")
        start_time = time.time()
        time.sleep(delay_seconds)
        actual_delay = time.time() - start_time

        return {"delayed_time": actual_delay}


class DataTransformNode(DataProcessingNode):
    """数据转换节点"""

    CONFIG_SCHEMA = {
        "transform_script": {
            "type": "string",
            "description": "数据转换脚本",
            "required": True,
        }
    }

    def _define_inputs(self) -> Dict[str, Dict[str, Any]]:
        return {
            "input_data": {"type": "any", "description": "输入数据", "required": True}
        }

    def _define_outputs(self) -> Dict[str, Dict[str, Any]]:
        return {"output_data": {"type": "any", "description": "转换后的数据"}}

    def process_data(self, input_data: Dict[str, Any], context) -> Dict[str, Any]:
        transform_script = self.get_config_value("transform_script")
        data = input_data.get("input_data")

        try:
            # 执行转换脚本
            local_vars = {"input_data": data, "output_data": None}

            exec(transform_script, {"__builtins__": {}}, local_vars)

            return {"output_data": local_vars.get("output_data", data)}

        except Exception as e:
            self.log_error(f"数据转换失败: {str(e)}")
            return {"output_data": data, "error": str(e)}


class FileOperationNode(ActionNode):
    """文件操作节点"""

    CONFIG_SCHEMA = {
        "operation": {
            "type": "string",
            "enum": ["read", "write", "append", "delete", "copy", "move"],
            "description": "文件操作类型",
            "required": True,
        },
        "file_path": {"type": "string", "description": "文件路径", "required": True},
    }

    def _define_inputs(self) -> Dict[str, Dict[str, Any]]:
        return {
            "content": {
                "type": "string",
                "description": "文件内容（写入时使用）",
                "required": False,
            },
            "target_path": {
                "type": "string",
                "description": "目标路径（复制/移动时使用）",
                "required": False,
            },
        }

    def _define_outputs(self) -> Dict[str, Dict[str, Any]]:
        return {
            "success": {"type": "boolean", "description": "操作是否成功"},
            "content": {"type": "string", "description": "文件内容（读取时返回）"},
        }

    def perform_action(self, input_data: Dict[str, Any], context) -> Dict[str, Any]:
        operation = self.get_config_value("operation")
        file_path = self.get_config_value("file_path")

        try:
            if operation == "read":
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return {"success": True, "content": content}

            elif operation == "write":
                content = input_data.get("content", "")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return {"success": True}

            elif operation == "append":
                content = input_data.get("content", "")
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write(content)
                return {"success": True}

            elif operation == "delete":
                import os

                os.remove(file_path)
                return {"success": True}

            elif operation in ["copy", "move"]:
                import shutil

                target_path = input_data.get("target_path")
                if not target_path:
                    raise ValueError("目标路径不能为空")

                if operation == "copy":
                    shutil.copy2(file_path, target_path)
                else:
                    shutil.move(file_path, target_path)

                return {"success": True}

            else:
                raise ValueError(f"不支持的文件操作: {operation}")

        except Exception as e:
            self.log_error(f"文件操作失败: {str(e)}")
            return {"success": False, "error": str(e)}


class DatabaseQueryNode(ActionNode):
    """数据库查询节点"""

    CONFIG_SCHEMA = {
        "query": {"type": "string", "description": "SQL查询语句", "required": True},
        "query_type": {
            "type": "string",
            "enum": ["select", "insert", "update", "delete"],
            "default": "select",
            "description": "查询类型",
        },
    }

    def _define_inputs(self) -> Dict[str, Dict[str, Any]]:
        return {
            "parameters": {"type": "list", "description": "SQL参数", "required": False}
        }

    def _define_outputs(self) -> Dict[str, Dict[str, Any]]:
        return {
            "results": {"type": "list", "description": "查询结果"},
            "row_count": {"type": "number", "description": "影响的行数"},
        }

    def perform_action(self, input_data: Dict[str, Any], context) -> Dict[str, Any]:
        query = self.get_config_value("query")
        query_type = self.get_config_value("query_type", "select")
        parameters = input_data.get("parameters", [])

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)

                if query_type == "select":
                    # 获取查询结果
                    columns = [col[0] for col in cursor.description]
                    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    return {"results": results, "row_count": len(results)}
                else:
                    # 获取影响的行数
                    row_count = cursor.rowcount
                    return {"results": [], "row_count": row_count}

        except Exception as e:
            self.log_error(f"数据库查询失败: {str(e)}")
            return {"results": [], "row_count": 0, "error": str(e)}
