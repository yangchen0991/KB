"""
文档管理信号处理
"""

import os

from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .models import Document, DocumentVersion


@receiver(post_delete, sender=Document)
def delete_document_files(sender, instance, **kwargs):
    """删除文档时清理相关文件"""
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)

    if instance.thumbnail:
        if os.path.isfile(instance.thumbnail.path):
            os.remove(instance.thumbnail.path)


@receiver(post_delete, sender=DocumentVersion)
def delete_version_files(sender, instance, **kwargs):
    """删除文档版本时清理文件"""
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)


@receiver(pre_save, sender=Document)
def update_file_info(sender, instance, **kwargs):
    """保存前更新文件信息"""
    if instance.file:
        instance.file_size = instance.file.size
        instance.file_type = instance.file.name.split(".")[-1].lower()
