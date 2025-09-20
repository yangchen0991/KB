"""
用户账户信号处理
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """创建用户时自动创建用户配置"""
    if created:
        UserProfile.objects.create(user=instance)
