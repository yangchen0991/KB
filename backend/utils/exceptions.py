"""
自定义异常处理
"""

import logging

from django.core.exceptions import ValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    自定义异常处理器
    """
    # 调用默认的异常处理器
    response = exception_handler(exc, context)

    # 记录异常日志
    if response is not None:
        logger.error(f"API Exception: {exc}", exc_info=True)

        custom_response_data = {
            "error": True,
            "message": "操作失败",
            "details": response.data,
            "status_code": response.status_code,
        }

        # 根据异常类型自定义错误消息
        if response.status_code == 400:
            custom_response_data["message"] = "请求参数错误"
        elif response.status_code == 401:
            custom_response_data["message"] = "未授权访问"
        elif response.status_code == 403:
            custom_response_data["message"] = "权限不足"
        elif response.status_code == 404:
            custom_response_data["message"] = "资源不存在"
        elif response.status_code == 405:
            custom_response_data["message"] = "请求方法不允许"
        elif response.status_code == 429:
            custom_response_data["message"] = "请求过于频繁"
        elif response.status_code >= 500:
            custom_response_data["message"] = "服务器内部错误"

        response.data = custom_response_data

    return response


class DocumentProcessingError(Exception):
    """文档处理异常"""

    pass


class ClassificationError(Exception):
    """分类异常"""

    pass


class SearchError(Exception):
    """搜索异常"""

    pass


class WorkflowError(Exception):
    """工作流异常"""

    pass


class MonitoringError(Exception):
    """监控异常"""

    pass
