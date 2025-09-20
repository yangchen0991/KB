"""
Elasticsearch 文档定义
"""

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from apps.documents.models import Document as DocumentModel


@registry.register_document
class DocumentDocument(Document):
    """文档搜索索引"""

    # 基本字段
    title = fields.TextField(
        analyzer="ik_max_word",
        search_analyzer="ik_smart",
        fields={
            "raw": fields.KeywordField(),
            "suggest": fields.CompletionField(),
        },
    )

    description = fields.TextField(analyzer="ik_max_word", search_analyzer="ik_smart")

    ocr_text = fields.TextField(analyzer="ik_max_word", search_analyzer="ik_smart")

    # 分类和标签
    category = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(
                analyzer="ik_max_word", fields={"raw": fields.KeywordField()}
            ),
            "full_path": fields.TextField(analyzer="ik_max_word"),
        }
    )

    tags = fields.NestedField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(
                analyzer="ik_max_word", fields={"raw": fields.KeywordField()}
            ),
        }
    )

    # 文件信息
    file_type = fields.KeywordField()
    file_size = fields.LongField()
    page_count = fields.IntegerField()

    # 用户信息
    uploaded_by = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "username": fields.KeywordField(),
            "full_name": fields.TextField(),
        }
    )

    # 状态和权限
    status = fields.KeywordField()
    is_public = fields.BooleanField()

    # OCR 相关
    ocr_confidence = fields.FloatField()
    ocr_language = fields.KeywordField()

    # 统计信息
    view_count = fields.IntegerField()
    download_count = fields.IntegerField()

    # 时间字段
    created_at = fields.DateField()
    updated_at = fields.DateField()

    # 全文搜索字段
    content = fields.TextField(analyzer="ik_max_word", search_analyzer="ik_smart")

    class Index:
        name = "documents"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "ik_max_word": {
                        "type": "custom",
                        "tokenizer": "ik_max_word",
                        "filter": ["lowercase", "stop"],
                    },
                    "ik_smart": {
                        "type": "custom",
                        "tokenizer": "ik_smart",
                        "filter": ["lowercase", "stop"],
                    },
                }
            },
        }

    class Django:
        model = DocumentModel
        fields = []  # 不自动包含模型字段

        related_models = ["documents.Category", "documents.Tag", "accounts.User"]

    def prepare_content(self, instance):
        """准备全文搜索内容"""
        content_parts = [
            instance.title,
            instance.description,
            instance.ocr_text,
        ]

        # 添加分类信息
        if instance.category:
            content_parts.append(instance.category.name)
            content_parts.append(instance.category.full_path)

        # 添加标签信息
        for tag in instance.tags.all():
            content_parts.append(tag.name)

        return " ".join(filter(None, content_parts))

    def prepare_category(self, instance):
        """准备分类信息"""
        if instance.category:
            return {
                "id": instance.category.id,
                "name": instance.category.name,
                "full_path": instance.category.full_path,
            }
        return None

    def prepare_tags(self, instance):
        """准备标签信息"""
        return [
            {
                "id": tag.id,
                "name": tag.name,
            }
            for tag in instance.tags.all()
        ]

    def prepare_uploaded_by(self, instance):
        """准备上传者信息"""
        return {
            "id": instance.uploaded_by.id,
            "username": instance.uploaded_by.username,
            "full_name": instance.uploaded_by.full_name,
        }

    def get_queryset(self):
        """获取查询集"""
        return (
            super()
            .get_queryset()
            .select_related("category", "uploaded_by")
            .prefetch_related("tags")
        )

    def should_index_object(self, obj):
        """判断是否应该索引对象"""
        return obj.status == "completed"
