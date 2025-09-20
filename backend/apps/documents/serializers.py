"""
文档管理序列化器
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Category,
    Document,
    DocumentComment,
    DocumentShare,
    DocumentVersion,
    Tag,
    DocumentActivity,
)

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """分类序列化器"""
    
    document_count = serializers.IntegerField(read_only=True)
    full_path = serializers.CharField(read_only=True)
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'color', 'icon', 'parent',
            'auto_classify', 'keywords', 'document_count', 'full_path',
            'created_at', 'updated_at'
        ]


class TagSerializer(serializers.ModelSerializer):
    """标签序列化器"""
    
    document_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'document_count', 'created_at']


class DocumentVersionSerializer(serializers.ModelSerializer):
    """文档版本序列化器"""
    
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    
    class Meta:
        model = DocumentVersion
        fields = [
            'id', 'version_number', 'file', 'comment',
            'uploaded_by', 'uploaded_by_name', 'created_at'
        ]
        read_only_fields = ['uploaded_by']


class DocumentCommentSerializer(serializers.ModelSerializer):
    """文档评论序列化器"""
    
    user_name = serializers.CharField(source='user.username', read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentComment
        fields = [
            'id', 'content', 'parent', 'user', 'user_name',
            'replies', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user']
    
    def get_replies(self, obj):
        if obj.replies.exists():
            return DocumentCommentSerializer(obj.replies.all(), many=True).data
        return []


class DocumentShareSerializer(serializers.ModelSerializer):
    """文档分享序列化器"""
    
    shared_by_name = serializers.CharField(source='shared_by.username', read_only=True)
    shared_with_name = serializers.CharField(source='shared_with.username', read_only=True)
    document_title = serializers.CharField(source='document.title', read_only=True)
    
    class Meta:
        model = DocumentShare
        fields = [
            'id', 'document', 'document_title', 'shared_by', 'shared_by_name',
            'shared_with', 'shared_with_name', 'permission', 'created_at'
        ]
        read_only_fields = ['shared_by', 'document']


class DocumentActivitySerializer(serializers.ModelSerializer):
    """文档活动序列化器"""
    
    user_name = serializers.CharField(source='user.username', read_only=True)
    document_title = serializers.CharField(source='document.title', read_only=True)
    
    class Meta:
        model = DocumentActivity
        fields = [
            'id', 'document', 'document_title', 'user', 'user_name',
            'action', 'description', 'created_at'
        ]


class DocumentSerializer(serializers.ModelSerializer):
    """文档序列化器"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    tags_data = TagSerializer(source='tags', many=True, read_only=True)
    file_size_human = serializers.CharField(read_only=True)
    
    # 统计字段
    comment_count = serializers.IntegerField(read_only=True)
    version_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'file', 'file_size', 'file_size_human',
            'file_type', 'file_hash', 'category', 'category_name', 'tags', 'tags_data',
            'uploaded_by', 'uploaded_by_name', 'status', 'processing_progress',
            'ocr_text', 'ocr_confidence', 'ocr_language', 'thumbnail', 'page_count',
            'metadata', 'is_public', 'view_count', 'download_count',
            'comment_count', 'version_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'uploaded_by', 'file_size', 'file_type', 'file_hash', 'status',
            'processing_progress', 'ocr_text', 'ocr_confidence', 'ocr_language',
            'thumbnail', 'page_count', 'metadata', 'view_count', 'download_count'
        ]
    
    def validate_file(self, value):
        """文件验证"""
        if not value:
            raise serializers.ValidationError("请选择要上传的文件")
        
        # 文件大小验证
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise serializers.ValidationError(f"文件大小不能超过 {max_size // (1024*1024)}MB")
        
        # 文件类型验证
        allowed_extensions = ['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'tiff']
        file_ext = value.name.split('.')[-1].lower()
        if file_ext not in allowed_extensions:
            raise serializers.ValidationError(f"不支持的文件类型: {file_ext}")
        
        return value


class DocumentDetailSerializer(DocumentSerializer):
    """文档详情序列化器"""
    
    versions = DocumentVersionSerializer(many=True, read_only=True)
    comments = DocumentCommentSerializer(many=True, read_only=True)
    shares = DocumentShareSerializer(many=True, read_only=True)
    recent_activities = serializers.SerializerMethodField()
    
    class Meta(DocumentSerializer.Meta):
        fields = DocumentSerializer.Meta.fields + [
            'versions', 'comments', 'shares', 'recent_activities'
        ]
    
    def get_recent_activities(self, obj):
        """获取最近活动"""
        activities = obj.activities.select_related('user').order_by('-created_at')[:10]
        return DocumentActivitySerializer(activities, many=True).data


class DocumentUploadSerializer(serializers.ModelSerializer):
    """文档上传序列化器"""
    
    class Meta:
        model = Document
        fields = ['title', 'description', 'file', 'category', 'tags', 'is_public']
    
    def create(self, validated_data):
        """创建文档并触发异步处理"""
        tags_data = validated_data.pop('tags', [])
        document = Document.objects.create(**validated_data)
        
        if tags_data:
            document.tags.set(tags_data)
        
        # 触发异步处理任务
        try:
            from .tasks import process_document_async
            process_document_async.delay(document.id)
        except ImportError:
            # 如果 Celery 不可用，同步处理
            pass
        
        return document


class BulkOperationSerializer(serializers.Serializer):
    """批量操作序列化器"""
    
    document_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="文档ID列表"
    )


class BulkCategorizeSerializer(BulkOperationSerializer):
    """批量分类序列化器"""
    
    category_id = serializers.IntegerField(help_text="分类ID")
    
    def validate_category_id(self, value):
        """验证分类是否存在"""
        try:
            Category.objects.get(id=value)
        except Category.DoesNotExist:
            raise serializers.ValidationError("分类不存在")
        return value


class BulkTagSerializer(BulkOperationSerializer):
    """批量标签序列化器"""
    
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="标签ID列表"
    )
    
    def validate_tag_ids(self, value):
        """验证标签是否存在"""
        existing_tags = Tag.objects.filter(id__in=value).count()
        if existing_tags != len(value):
            raise serializers.ValidationError("部分标签不存在")
        return value


class DocumentSearchSerializer(serializers.Serializer):
    """文档搜索序列化器"""
    
    query = serializers.CharField(max_length=255, help_text="搜索关键词")
    category = serializers.IntegerField(required=False, help_text="分类ID")
    tags = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="标签ID列表"
    )
    file_type = serializers.CharField(max_length=50, required=False, help_text="文件类型")
    date_from = serializers.DateTimeField(required=False, help_text="开始日期")
    date_to = serializers.DateTimeField(required=False, help_text="结束日期")
    sort_by = serializers.ChoiceField(
        choices=[
            ('relevance', '相关性'),
            ('created_at', '创建时间'),
            ('updated_at', '更新时间'),
            ('view_count', '查看次数'),
            ('download_count', '下载次数'),
        ],
        default='relevance',
        help_text="排序方式"
    )
    page = serializers.IntegerField(min_value=1, default=1, help_text="页码")
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20, help_text="每页数量")