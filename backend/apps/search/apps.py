"""
搜索应用配置
"""

from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.search"
    verbose_name = "搜索系统"

    def ready(self):
        """应用就绪时导入信号处理器"""
        # 只在非测试环境导入信号处理器
        import os

        if "test" not in os.environ.get("DJANGO_SETTINGS_MODULE", ""):
            try:
                import apps.search.signals
            except Exception as e:
                # 如果Elasticsearch不可用，记录警告但不阻止应用启动
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"搜索功能暂时不可用: {e}")
