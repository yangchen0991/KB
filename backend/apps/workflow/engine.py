"""
工作流执行引擎核心模块
实现工作流的执行、调度和状态管理
"""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .exceptions import NodeExecutionError, WorkflowExecutionError
from .models import NodeExecution, WorkflowExecution, WorkflowTemplate, WorkflowVariable
from .nodes import BaseNode, NodeRegistry

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """工作流执行引擎"""

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.node_registry = NodeRegistry()
        self.running_executions: Dict[str, WorkflowExecution] = {}

    def register_node_type(self, node_type: str, node_class: type):
        """注册节点类型"""
        self.node_registry.register(node_type, node_class)

    def execute_workflow(
        self,
        template: WorkflowTemplate,
        input_data: Dict[str, Any],
        user,
        priority: str = "normal",
    ) -> WorkflowExecution:
        """执行工作流"""
        try:
            # 创建执行实例
            execution = WorkflowExecution.objects.create(
                template=template,
                input_data=input_data,
                priority=priority,
                created_by=user,
                status="pending",
            )

            # 异步执行工作流
            self._execute_workflow_async(execution)

            return execution

        except Exception as e:
            logger.error(f"工作流执行失败: {str(e)}")
            raise WorkflowExecutionError(f"工作流执行失败: {str(e)}")

    def _execute_workflow_async(self, execution: WorkflowExecution):
        """异步执行工作流"""
        self.executor.submit(self._run_workflow, execution)

    def _run_workflow(self, execution: WorkflowExecution):
        """运行工作流"""
        try:
            with transaction.atomic():
                # 更新状态为运行中
                execution.status = "running"
                execution.started_at = timezone.now()
                execution.save()

                # 添加到运行中的执行列表
                self.running_executions[str(execution.id)] = execution

                logger.info(
                    f"开始执行工作流: {execution.template.name} (ID: {execution.id})"
                )

                # 解析工作流定义
                workflow_def = execution.template.definition
                nodes = workflow_def.get("nodes", [])
                edges = workflow_def.get("edges", [])

                # 构建执行图
                execution_graph = self._build_execution_graph(nodes, edges)

                # 初始化执行上下文
                context = ExecutionContext(
                    execution=execution,
                    input_data=execution.input_data,
                    variables=self._load_variables(execution),
                )

                # 执行工作流
                self._execute_graph(execution_graph, context)

                # 更新执行状态
                execution.status = "completed"
                execution.completed_at = timezone.now()
                execution.output_data = context.output_data
                execution.context = context.to_dict()
                execution.save()

                # 更新模板统计
                execution.template.execution_count += 1
                execution.template.success_count += 1
                execution.template.save()

                logger.info(f"工作流执行完成: {execution.id}")

        except Exception as e:
            logger.error(f"工作流执行失败: {execution.id}, 错误: {str(e)}")

            # 更新执行状态为失败
            execution.status = "failed"
            execution.completed_at = timezone.now()
            execution.error_message = str(e)
            execution.save()

            # 更新模板统计
            execution.template.execution_count += 1
            execution.template.save()

        finally:
            # 从运行中的执行列表移除
            self.running_executions.pop(str(execution.id), None)

    def _build_execution_graph(
        self, nodes: List[Dict], edges: List[Dict]
    ) -> "ExecutionGraph":
        """构建执行图"""
        graph = ExecutionGraph()

        # 添加节点
        for node_def in nodes:
            node_id = node_def["id"]
            node_type = node_def["type"]
            node_config = node_def.get("config", {})

            # 创建节点实例
            node_class = self.node_registry.get_node_class(node_type)
            if not node_class:
                raise WorkflowExecutionError(f"未知的节点类型: {node_type}")

            node = node_class(node_id, node_config)
            graph.add_node(node)

        # 添加边
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            condition = edge.get("condition")

            graph.add_edge(source, target, condition)

        return graph

    def _execute_graph(self, graph: "ExecutionGraph", context: "ExecutionContext"):
        """执行图"""
        # 获取起始节点
        start_nodes = graph.get_start_nodes()
        if not start_nodes:
            raise WorkflowExecutionError("工作流没有起始节点")

        # 执行队列
        execution_queue = list(start_nodes)
        executed_nodes = set()

        while execution_queue:
            current_node = execution_queue.pop(0)

            if current_node.id in executed_nodes:
                continue

            # 检查前置条件
            if not self._check_prerequisites(current_node, graph, executed_nodes):
                execution_queue.append(current_node)  # 重新加入队列
                continue

            # 执行节点
            self._execute_node(current_node, context)
            executed_nodes.add(current_node.id)

            # 获取下一个节点
            next_nodes = graph.get_next_nodes(current_node.id, context)
            execution_queue.extend(next_nodes)

    def _check_prerequisites(
        self, node: BaseNode, graph: "ExecutionGraph", executed_nodes: set
    ) -> bool:
        """检查节点前置条件"""
        predecessors = graph.get_predecessors(node.id)
        return all(pred.id in executed_nodes for pred in predecessors)

    def _execute_node(self, node: BaseNode, context: "ExecutionContext"):
        """执行单个节点"""
        try:
            # 创建节点执行记录
            node_execution = NodeExecution.objects.create(
                workflow_execution=context.execution,
                node_id=node.id,
                node_type=node.node_type,
                node_name=node.name,
                status="running",
                started_at=timezone.now(),
            )

            logger.info(f"开始执行节点: {node.name} (ID: {node.id})")

            # 准备输入数据
            input_data = self._prepare_node_input(node, context)
            node_execution.input_data = input_data
            node_execution.save()

            # 执行节点
            output_data = node.execute(input_data, context)

            # 更新节点执行记录
            node_execution.status = "completed"
            node_execution.completed_at = timezone.now()
            node_execution.output_data = output_data
            node_execution.save()

            # 更新上下文
            context.set_node_output(node.id, output_data)

            logger.info(f"节点执行完成: {node.id}")

        except Exception as e:
            logger.error(f"节点执行失败: {node.id}, 错误: {str(e)}")

            # 更新节点执行记录
            node_execution.status = "failed"
            node_execution.completed_at = timezone.now()
            node_execution.error_message = str(e)
            node_execution.save()

            raise NodeExecutionError(f"节点 {node.id} 执行失败: {str(e)}")

    def _prepare_node_input(
        self, node: BaseNode, context: "ExecutionContext"
    ) -> Dict[str, Any]:
        """准备节点输入数据"""
        input_data = {}

        # 从上下文获取输入数据
        for input_name, input_config in node.inputs.items():
            if "source" in input_config:
                source = input_config["source"]
                if source.startswith("$"):
                    # 变量引用
                    var_name = source[1:]
                    input_data[input_name] = context.get_variable(var_name)
                elif "." in source:
                    # 节点输出引用
                    node_id, output_name = source.split(".", 1)
                    node_output = context.get_node_output(node_id)
                    input_data[input_name] = node_output.get(output_name)
                else:
                    # 直接值
                    input_data[input_name] = source
            elif "default" in input_config:
                input_data[input_name] = input_config["default"]

        return input_data

    def _load_variables(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """加载工作流变量"""
        variables = {}

        # 加载全局变量
        global_vars = WorkflowVariable.objects.filter(scope="global")
        for var in global_vars:
            variables[var.name] = var.value

        # 加载模板变量
        template_vars = WorkflowVariable.objects.filter(
            scope="template", template=execution.template
        )
        for var in template_vars:
            variables[var.name] = var.value

        # 加载执行实例变量
        execution_vars = WorkflowVariable.objects.filter(
            scope="execution", execution=execution
        )
        for var in execution_vars:
            variables[var.name] = var.value

        return variables

    def pause_execution(self, execution_id: str) -> bool:
        """暂停工作流执行"""
        try:
            execution = WorkflowExecution.objects.get(id=execution_id)
            if execution.status == "running":
                execution.status = "paused"
                execution.save()
                return True
            return False
        except WorkflowExecution.DoesNotExist:
            return False

    def resume_execution(self, execution_id: str) -> bool:
        """恢复工作流执行"""
        try:
            execution = WorkflowExecution.objects.get(id=execution_id)
            if execution.status == "paused":
                execution.status = "running"
                execution.save()
                # 重新提交执行
                self._execute_workflow_async(execution)
                return True
            return False
        except WorkflowExecution.DoesNotExist:
            return False

    def cancel_execution(self, execution_id: str) -> bool:
        """取消工作流执行"""
        try:
            execution = WorkflowExecution.objects.get(id=execution_id)
            if execution.status in ["pending", "running", "paused"]:
                execution.status = "cancelled"
                execution.completed_at = timezone.now()
                execution.save()

                # 从运行中的执行列表移除
                self.running_executions.pop(execution_id, None)
                return True
            return False
        except WorkflowExecution.DoesNotExist:
            return False

    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取执行状态"""
        try:
            execution = WorkflowExecution.objects.get(id=execution_id)
            node_executions = execution.node_executions.all()

            return {
                "id": str(execution.id),
                "status": execution.status,
                "started_at": execution.started_at,
                "completed_at": execution.completed_at,
                "duration": execution.duration,
                "progress": self._calculate_progress(node_executions),
                "nodes": [
                    {
                        "id": node.node_id,
                        "name": node.node_name,
                        "status": node.status,
                        "duration": node.duration,
                        "error_message": node.error_message,
                    }
                    for node in node_executions
                ],
            }
        except WorkflowExecution.DoesNotExist:
            return None

    def _calculate_progress(self, node_executions) -> float:
        """计算执行进度"""
        if not node_executions:
            return 0.0

        completed_count = sum(
            1 for node in node_executions if node.status in ["completed", "skipped"]
        )
        total_count = len(node_executions)

        return round((completed_count / total_count) * 100, 2)


class ExecutionGraph:
    """执行图"""

    def __init__(self):
        self.nodes: Dict[str, BaseNode] = {}
        self.edges: Dict[str, List[Dict]] = {}
        self.predecessors: Dict[str, List[BaseNode]] = {}

    def add_node(self, node: BaseNode):
        """添加节点"""
        self.nodes[node.id] = node
        self.edges[node.id] = []
        self.predecessors[node.id] = []

    def add_edge(self, source: str, target: str, condition: Optional[str] = None):
        """添加边"""
        edge = {"target": target, "condition": condition}
        self.edges[source].append(edge)

        if target in self.nodes:
            self.predecessors[target].append(self.nodes[source])

    def get_start_nodes(self) -> List[BaseNode]:
        """获取起始节点"""
        return [
            node
            for node_id, node in self.nodes.items()
            if not self.predecessors[node_id]
        ]

    def get_next_nodes(
        self, node_id: str, context: "ExecutionContext"
    ) -> List[BaseNode]:
        """获取下一个节点"""
        next_nodes = []

        for edge in self.edges.get(node_id, []):
            target_id = edge["target"]
            condition = edge.get("condition")

            # 检查条件
            if not condition or self._evaluate_condition(condition, context):
                if target_id in self.nodes:
                    next_nodes.append(self.nodes[target_id])

        return next_nodes

    def get_predecessors(self, node_id: str) -> List[BaseNode]:
        """获取前驱节点"""
        return self.predecessors.get(node_id, [])

    def _evaluate_condition(self, condition: str, context: "ExecutionContext") -> bool:
        """评估条件表达式"""
        try:
            # 简单的条件评估，可以扩展为更复杂的表达式解析
            # 支持格式: ${variable} == 'value'
            # TODO: 实现更完整的表达式解析器
            return True
        except Exception:
            return False


class ExecutionContext:
    """执行上下文"""

    def __init__(
        self,
        execution: WorkflowExecution,
        input_data: Dict[str, Any],
        variables: Dict[str, Any],
    ):
        self.execution = execution
        self.input_data = input_data
        self.variables = variables
        self.node_outputs: Dict[str, Dict[str, Any]] = {}
        self.output_data: Dict[str, Any] = {}

    def get_variable(self, name: str) -> Any:
        """获取变量值"""
        return self.variables.get(name)

    def set_variable(self, name: str, value: Any):
        """设置变量值"""
        self.variables[name] = value

    def get_node_output(self, node_id: str) -> Dict[str, Any]:
        """获取节点输出"""
        return self.node_outputs.get(node_id, {})

    def set_node_output(self, node_id: str, output: Dict[str, Any]):
        """设置节点输出"""
        self.node_outputs[node_id] = output

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "variables": self.variables,
            "node_outputs": self.node_outputs,
            "output_data": self.output_data,
        }


# 全局工作流引擎实例
workflow_engine = WorkflowEngine()
