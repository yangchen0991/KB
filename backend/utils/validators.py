"""
自定义验证器
"""

import os

import magic
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_file_size(file):
    """验证文件大小"""
    max_size = getattr(settings, "MAX_UPLOAD_SIZE", 100 * 1024 * 1024)  # 100MB
    if file.size > max_size:
        raise ValidationError(
            _("文件大小不能超过 %(max_size)s MB"),
            params={"max_size": max_size // (1024 * 1024)},
        )


def validate_file_type(file):
    """验证文件类型"""
    allowed_types = getattr(
        settings,
        "ALLOWED_FILE_TYPES",
        [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "text/plain",
            "text/csv",
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/bmp",
            "image/tiff",
        ],
    )

    # 使用python-magic检测文件类型
    file_type = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)  # 重置文件指针

    if file_type not in allowed_types:
        raise ValidationError(
            _("不支持的文件类型: %(file_type)s"), params={"file_type": file_type}
        )


def validate_image_file(file):
    """验证图像文件"""
    image_types = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/bmp",
        "image/tiff",
    ]

    file_type = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)

    if file_type not in image_types:
        raise ValidationError(_("必须是图像文件"))


def validate_document_file(file):
    """验证文档文件"""
    document_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/plain",
        "text/csv",
    ]

    file_type = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)

    if file_type not in document_types:
        raise ValidationError(_("必须是文档文件"))


def validate_cron_expression(value):
    """验证Cron表达式"""
    try:
        from croniter import croniter

        croniter(value)
    except (ValueError, TypeError):
        raise ValidationError(_("无效的Cron表达式"))


def validate_json_schema(value, schema):
    """验证JSON模式"""
    try:
        import jsonschema

        jsonschema.validate(value, schema)
    except jsonschema.ValidationError as e:
        raise ValidationError(f"JSON格式错误: {e.message}")
    except jsonschema.SchemaError as e:
        raise ValidationError(f"JSON模式错误: {e.message}")


def validate_workflow_config(value):
    """验证工作流配置"""
    required_fields = ["steps", "name"]

    if not isinstance(value, dict):
        raise ValidationError(_("工作流配置必须是JSON对象"))

    for field in required_fields:
        if field not in value:
            raise ValidationError(
                _("工作流配置缺少必需字段: %(field)s"), params={"field": field}
            )

    if not isinstance(value.get("steps"), list):
        raise ValidationError(_("工作流步骤必须是数组"))

    if len(value["steps"]) == 0:
        raise ValidationError(_("工作流至少需要一个步骤"))


def validate_ip_address_list(value):
    """验证IP地址列表"""
    import ipaddress

    if not isinstance(value, list):
        raise ValidationError(_("IP地址列表必须是数组"))

    for ip in value:
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            raise ValidationError(_("无效的IP地址: %(ip)s"), params={"ip": ip})
