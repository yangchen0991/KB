"""
节点注册表
管理所有可用的节点类型
"""

import logging
from typing import Dict, Optional, Type

from .base import BaseNode

logger = logging.getLogger(__name__)


class NodeRegistry:
    """节点注册表"""

    def __init__(self):
        self._nodes: Dict[str, Type[BaseNode]] = {}
        self._register_builtin_nodes()

    def register(self, node_type: str, node_class: Type[BaseNode]):
        """注册节点类型"""
        if not issubclass(node_class, BaseNode):
            raise ValueError(f"节点类 {node_class} 必须继承自 BaseNode")

        self._nodes[node_type] = node_class
        logger.info(f"注册节点类型: {node_type} -> {node_class.__name__}")

    def unregister(self, node_type: str):
        """注销节点类型"""
        if node_type in self._nodes:
            del self._nodes[node_type]
            logger.info(f"注销节点类型: {node_type}")

    def get_node_class(self, node_type: str) -> Optional[Type[BaseNode]]:
        """获取节点类"""
        return self._nodes.get(node_type)

    def get_available_types(self) -> Dict[str, Type[BaseNode]]:
        """获取所有可用的节点类型"""
        return self._nodes.copy()

    def create_node(
        self, node_type: str, node_id: str, config: Dict
    ) -> Optional[BaseNode]:
        """创建节点实例"""
        node_class = self.get_node_class(node_type)
        if node_class:
            return node_class(node_id, config)
        return None

    def _register_builtin_nodes(self):
        """注册内置节点类型"""
        from .builtin import (
            ConditionNode,
            DatabaseQueryNode,
            DataTransformNode,
            DelayNode,
            EmailNode,
            EndNode,
            FileOperationNode,
            HttpRequestNode,
            ScriptNode,
            StartNode,
        )

        # 注册内置节点
        builtin_nodes = [
            ("start", StartNode),
            ("end", EndNode),
            ("condition", ConditionNode),
            ("script", ScriptNode),
            ("http_request", HttpRequestNode),
            ("email", EmailNode),
            ("delay", DelayNode),
            ("data_transform", DataTransformNode),
            ("file_operation", FileOperationNode),
            ("database_query", DatabaseQueryNode),
        ]

        for node_type, node_class in builtin_nodes:
            self.register(node_type, node_class)

    def get_node_schema(self, node_type: str) -> Optional[Dict]:
        """获取节点模式定义"""
        node_class = self.get_node_class(node_type)
        if not node_class:
            return None

        # 创建临时实例获取输入输出定义
        temp_node = node_class("temp", {})

        return {
            "type": node_type,
            "name": node_class.__name__,
            "description": node_class.__doc__ or "",
            "inputs": temp_node.inputs,
            "outputs": temp_node.outputs,
            "config_schema": getattr(node_class, "CONFIG_SCHEMA", {}),
        }

    def get_all_schemas(self) -> Dict[str, Dict]:
        """获取所有节点的模式定义"""
        schemas = {}
        for node_type in self._nodes:
            schema = self.get_node_schema(node_type)
            if schema:
                schemas[node_type] = schema
        return schemas


# 全局节点注册表实例
node_registry = NodeRegistry()
