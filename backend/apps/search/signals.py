"""
搜索系统信号处理 - 自动索引更新
"""

import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.documents.models import Document

from .tasks import delete_document_index_task, index_document_task

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Document)
def document_saved_handler(sender, instance, created, **kwargs):
    """文档保存后自动更新索引"""
    try:
        # 异步更新索引
        index_document_task.delay(instance.id)

        if created:
            logger.info(f"新文档 {instance.id} 已加入索引队列")
        else:
            logger.info(f"文档 {instance.id} 索引更新已加入队列")

    except Exception as e:
        logger.error(f"文档 {instance.id} 索引更新失败: {e}")


@receiver(post_delete, sender=Document)
def document_deleted_handler(sender, instance, **kwargs):
    """文档删除后自动删除索引"""
    try:
        # 异步删除索引
        delete_document_index_task.delay(instance.id)
        logger.info(f"文档 {instance.id} 索引删除已加入队列")

    except Exception as e:
        logger.error(f"文档 {instance.id} 索引删除失败: {e}")
