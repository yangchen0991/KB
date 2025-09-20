"""
用户账户应用配置
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "用户账户"

    def ready(self):
        import apps.accounts.signals
