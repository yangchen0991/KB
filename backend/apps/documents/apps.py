"""
文档管理应用配置
"""

from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.documents"
    verbose_name = "文档管理"

    def ready(self):
        import apps.documents.signals
