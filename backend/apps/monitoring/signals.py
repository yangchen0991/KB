"""
监控系统信号处理器
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()

@receiver(post_save, sender=User)
def user_created_handler(sender, instance, created, **kwargs):
    """用户创建信号处理"""
    if created:
        logger.info(f"新用户注册: {instance.username}")

# 可以添加更多信号处理器
