from django.apps import AppConfig

class WorkflowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.workflow'
    verbose_name = '工作流引擎'
    
    def ready(self):
        """应用就绪时的初始化"""
        try:
            # 导入信号处理器
            from . import signals
        except ImportError:
            pass
