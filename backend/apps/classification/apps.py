"""
文档分类应用配置
"""

from django.apps import AppConfig


class ClassificationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.classification"
    verbose_name = "文档分类"
