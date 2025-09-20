"""
搜索系统异步任务
"""

import logging

from celery import shared_task
from django.apps import apps

from .elasticsearch_client import get_es_client

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def index_document_task(self, document_id: int):
    """异步索引单个文档"""
    try:
        Document = apps.get_model("documents", "Document")
        document = (
            Document.objects.select_related("category", "uploaded_by")
            .prefetch_related("tags")
            .get(id=document_id)
        )

        # 构建索引数据
        index_data = {
            "id": document.id,
            "title": document.title,
            "description": document.description or "",
            "content": getattr(document, "content", ""),
            "ocr_text": document.ocr_text or "",
            "file_type": document.file_type,
            "file_size": document.file_size,
            "category": {
                "id": document.category.id if document.category else None,
                "name": document.category.name if document.category else None,
            },
            "tags": [{"id": tag.id, "name": tag.name} for tag in document.tags.all()],
            "uploaded_by": {
                "id": document.uploaded_by.id,
                "username": document.uploaded_by.username,
            },
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat(),
            "view_count": document.view_count,
            "download_count": document.download_count,
            "is_public": document.is_public,
        }

        # 执行索引
        es_client = get_es_client()
        if not es_client:
            logger.warning("Elasticsearch客户端不可用，跳过索引任务")
            return False

        success = es_client.index_document(document_id, index_data)

        if success:
            logger.info(f"文档 {document_id} 索引成功")
        else:
            raise Exception("索引失败")

    except Document.DoesNotExist:
        logger.error(f"文档 {document_id} 不存在")
    except Exception as e:
        logger.error(f"索引文档 {document_id} 失败: {e}")
        # 重试
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2**self.request.retries))
        else:
            logger.error(f"文档 {document_id} 索引最终失败")


@shared_task(bind=True, max_retries=3)
def delete_document_index_task(self, document_id: int):
    """异步删除文档索引"""
    try:
        es_client = get_es_client()
        if not es_client:
            logger.warning("Elasticsearch客户端不可用，跳过删除任务")
            return False

        success = es_client.delete_document(document_id)

        if success:
            logger.info(f"文档 {document_id} 索引删除成功")
        else:
            raise Exception("删除索引失败")

    except Exception as e:
        logger.error(f"删除文档 {document_id} 索引失败: {e}")
        # 重试
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2**self.request.retries))


@shared_task
def bulk_reindex_documents():
    """批量重建索引"""
    try:
        Document = apps.get_model("documents", "Document")

        # 获取所有文档
        documents = (
            Document.objects.select_related("category", "uploaded_by")
            .prefetch_related("tags")
            .all()
        )

        logger.info(f"开始批量重建索引，共 {documents.count()} 个文档")

        # 构建索引数据
        index_data_list = []
        for document in documents:
            index_data = {
                "id": document.id,
                "title": document.title,
                "description": document.description or "",
                "content": getattr(document, "content", ""),
                "ocr_text": document.ocr_text or "",
                "file_type": document.file_type,
                "file_size": document.file_size,
                "category": {
                    "id": document.category.id if document.category else None,
                    "name": document.category.name if document.category else None,
                },
                "tags": [
                    {"id": tag.id, "name": tag.name} for tag in document.tags.all()
                ],
                "uploaded_by": {
                    "id": document.uploaded_by.id,
                    "username": document.uploaded_by.username,
                },
                "created_at": document.created_at.isoformat(),
                "updated_at": document.updated_at.isoformat(),
                "view_count": document.view_count,
                "download_count": document.download_count,
                "is_public": document.is_public,
            }
            index_data_list.append(index_data)

        # 批量索引
        es_client = get_es_client()
        if not es_client:
            logger.warning("Elasticsearch客户端不可用，跳过批量索引任务")
            return False

        success = es_client.bulk_index_documents(index_data_list)

        if success:
            logger.info("批量重建索引成功")
        else:
            logger.error("批量重建索引失败")

    except Exception as e:
        logger.error(f"批量重建索引失败: {e}")


@shared_task
def optimize_search_index():
    """优化搜索索引"""
    try:
        es_client = get_es_client()
        if es_client and es_client.client:
            # 强制合并索引段
            es_client.client.indices.forcemerge(
                index=es_client.index_name, max_num_segments=1
            )

            # 刷新索引
            es_client.client.indices.refresh(index=es_client.index_name)

            logger.info("搜索索引优化完成")
        else:
            logger.warning("Elasticsearch客户端不可用")

    except Exception as e:
        logger.error(f"优化搜索索引失败: {e}")


@shared_task
def cleanup_search_history():
    """清理搜索历史"""
    try:
        from datetime import datetime, timedelta

        from .models import SearchHistory

        # 删除30天前的搜索历史
        cutoff_date = datetime.now() - timedelta(days=30)
        deleted_count = SearchHistory.objects.filter(
            created_at__lt=cutoff_date
        ).delete()[0]

        logger.info(f"清理搜索历史完成，删除 {deleted_count} 条记录")

    except Exception as e:
        logger.error(f"清理搜索历史失败: {e}")


@shared_task
def update_search_suggestions():
    """更新搜索建议"""
    try:
        from django.db.models import Count

        from .models import SearchHistory, SearchSuggestion

        # 获取热门搜索词
        popular_queries = (
            SearchHistory.objects.values("query")
            .annotate(count=Count("query"))
            .filter(count__gte=5)
            .order_by("-count")[:100]
        )

        # 更新搜索建议
        SearchSuggestion.objects.all().delete()

        suggestions = []
        for item in popular_queries:
            suggestions.append(
                SearchSuggestion(query=item["query"], frequency=item["count"])
            )

        SearchSuggestion.objects.bulk_create(suggestions)

        logger.info(f"更新搜索建议完成，共 {len(suggestions)} 条")

    except Exception as e:
        logger.error(f"更新搜索建议失败: {e}")
