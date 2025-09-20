"""
工作流节点基类
定义节点的基本接口和行为
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..execution import ExecutionContext
else:
    ExecutionContext = object

logger = logging.getLogger(__name__)


class BaseNode(ABC):
    """工作流节点基类"""

    def __init__(self, node_id: str, config: Dict[str, Any]):
        self.id = node_id
        self.config = config
        self.name = config.get("name", node_id)
        self.description = config.get("description", "")

        # 节点输入输出定义
        self.inputs = self._define_inputs()
        self.outputs = self._define_outputs()

        # 节点类型
        self.node_type = self.__class__.__name__.lower().replace("node", "")

    @abstractmethod
    def _define_inputs(self) -> Dict[str, Dict[str, Any]]:
        """定义节点输入"""
        pass

    @abstractmethod
    def _define_outputs(self) -> Dict[str, Dict[str, Any]]:
        """定义节点输出"""
        pass

    @abstractmethod
    def execute(
        self, input_data: Dict[str, Any], context: "ExecutionContext"
    ) -> Dict[str, Any]:
        """执行节点逻辑"""
        pass

    def validate_inputs(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        for input_name, input_def in self.inputs.items():
            if input_def.get("required", False) and input_name not in input_data:
                raise ValueError(f"缺少必需的输入参数: {input_name}")

            if input_name in input_data:
                expected_type = input_def.get("type")
                if expected_type and not self._check_type(
                    input_data[input_name], expected_type
                ):
                    raise ValueError(
                        f"输入参数 {input_name} 类型错误，期望: {expected_type}"
                    )

        return True

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查数据类型"""
        type_mapping = {
            "string": str,
            "number": (int, float),
            "boolean": bool,
            "list": list,
            "dict": dict,
            "any": object,
        }

        expected_python_type = type_mapping.get(expected_type, object)
        return isinstance(value, expected_python_type)

    def log_info(self, message: str):
        """记录信息日志"""
        logger.info(f"[{self.node_type}:{self.id}] {message}")

    def log_error(self, message: str):
        """记录错误日志"""
        logger.error(f"[{self.node_type}:{self.id}] {message}")

    def log_warning(self, message: str):
        """记录警告日志"""
        logger.warning(f"[{self.node_type}:{self.id}] {message}")

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)

    def __str__(self):
        return f"{self.node_type}:{self.id}"

    def __repr__(self):
        return f"<{self.__class__.__name__}(id='{self.id}', name='{self.name}')>"


class ConditionalNode(BaseNode):
    """条件节点基类"""

    def _define_outputs(self) -> Dict[str, Dict[str, Any]]:
        return {"condition_result": {"type": "boolean", "description": "条件判断结果"}}

    @abstractmethod
    def evaluate_condition(
        self, input_data: Dict[str, Any], context: "ExecutionContext"
    ) -> bool:
        """评估条件"""
        pass

    def execute(
        self, input_data: Dict[str, Any], context: "ExecutionContext"
    ) -> Dict[str, Any]:
        """执行条件判断"""
        self.validate_inputs(input_data)

        try:
            result = self.evaluate_condition(input_data, context)
            self.log_info(f"条件判断结果: {result}")

            return {"condition_result": result}
        except Exception as e:
            self.log_error(f"条件判断失败: {str(e)}")
            raise


class ActionNode(BaseNode):
    """动作节点基类"""

    @abstractmethod
    def perform_action(
        self, input_data: Dict[str, Any], context: "ExecutionContext"
    ) -> Dict[str, Any]:
        """执行动作"""
        pass

    def execute(
        self, input_data: Dict[str, Any], context: "ExecutionContext"
    ) -> Dict[str, Any]:
        """执行动作"""
        self.validate_inputs(input_data)

        try:
            self.log_info("开始执行动作")
            result = self.perform_action(input_data, context)
            self.log_info("动作执行完成")

            return result
        except Exception as e:
            self.log_error(f"动作执行失败: {str(e)}")
            raise


class DataProcessingNode(BaseNode):
    """数据处理节点基类"""

    @abstractmethod
    def process_data(
        self, input_data: Dict[str, Any], context: "ExecutionContext"
    ) -> Dict[str, Any]:
        """处理数据"""
        pass

    def execute(
        self, input_data: Dict[str, Any], context: "ExecutionContext"
    ) -> Dict[str, Any]:
        """执行数据处理"""
        self.validate_inputs(input_data)

        try:
            self.log_info("开始处理数据")
            result = self.process_data(input_data, context)
            self.log_info("数据处理完成")

            return result
        except Exception as e:
            self.log_error(f"数据处理失败: {str(e)}")
            raise
