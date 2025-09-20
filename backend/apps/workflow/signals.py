"""
工作流信号处理
"""

import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import NodeExecution, WorkflowExecution

logger = logging.getLogger(__name__)


@receiver(post_save, sender=WorkflowExecution)
def workflow_execution_post_save(sender, instance, created, **kwargs):
    """工作流执行保存后处理"""
    if created:
        logger.info(f"新的工作流执行创建: {instance.id}")

    # 如果状态变为完成，更新模板统计
    if instance.status in ["completed", "failed"]:
        logger.info(f"工作流执行结束: {instance.id}, 状态: {instance.status}")


@receiver(post_save, sender=NodeExecution)
def node_execution_post_save(sender, instance, created, **kwargs):
    """节点执行保存后处理"""
    if created:
        logger.info(
            f"新的节点执行创建: {instance.workflow_execution.id}:{instance.node_id}"
        )

    # 如果节点执行失败，记录错误
    if instance.status == "failed":
        logger.error(
            f"节点执行失败: {instance.workflow_execution.id}:{instance.node_id}, 错误: {instance.error_message}"
        )


@receiver(post_delete, sender=WorkflowExecution)
def workflow_execution_post_delete(sender, instance, **kwargs):
    """工作流执行删除后处理"""
    logger.info(f"工作流执行已删除: {instance.id}")
