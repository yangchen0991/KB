from django.apps import AppConfig

class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.monitoring'
    verbose_name = '监控系统'
    
    def ready(self):
        """应用就绪时的初始化"""
        try:
            # 导入信号处理器
            from . import signals
        except ImportError:
            pass
        
        # 启动监控收集器（仅在主进程中）
        import os
        if os.environ.get('RUN_MAIN') != 'true':
            try:
                from .collectors import start_collectors
                start_collectors()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"监控收集器启动失败: {e}")
