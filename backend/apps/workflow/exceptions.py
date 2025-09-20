"""
工作流引擎异常定义
"""


class WorkflowException(Exception):
    """工作流基础异常"""

    pass


class WorkflowExecutionError(WorkflowException):
    """工作流执行异常"""

    pass


class NodeExecutionError(WorkflowException):
    """节点执行异常"""

    pass


class WorkflowValidationError(WorkflowException):
    """工作流验证异常"""

    pass


class NodeRegistrationError(WorkflowException):
    """节点注册异常"""

    pass


class ScheduleError(WorkflowException):
    """调度异常"""

    pass
