"""
搜索序列化器
"""

from rest_framework import serializers
from .models import SearchQuery, PopularSearch, SearchIndex


class SearchQuerySerializer(serializers.ModelSerializer):
    """搜索查询序列化器"""
    
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = SearchQuery
        fields = [
            'id', 'query', 'filters', 'results_count', 'execution_time',
            'user', 'user_name', 'created_at'
        ]
        read_only_fields = ['user']


class PopularSearchSerializer(serializers.ModelSerializer):
    """热门搜索序列化器"""
    
    class Meta:
        model = PopularSearch
        fields = ['id', 'query', 'search_count', 'last_searched']


class SearchIndexSerializer(serializers.ModelSerializer):
    """搜索索引序列化器"""
    
    document_title = serializers.CharField(source='document.title', read_only=True)
    
    class Meta:
        model = SearchIndex
        fields = [
            'id', 'document', 'document_title', 'status', 
            'indexed_content', 'keywords', 'created_at', 'updated_at'
        ]


class DocumentSearchSerializer(serializers.Serializer):
    """文档搜索请求序列化器"""
    
    query = serializers.CharField(max_length=500, help_text="搜索关键词")
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


class AdvancedSearchSerializer(serializers.Serializer):
    """高级搜索请求序列化器"""
    
    title = serializers.CharField(max_length=255, required=False, help_text="标题包含")
    content = serializers.CharField(max_length=500, required=False, help_text="内容包含")
    category = serializers.IntegerField(required=False, help_text="分类ID")
    tags = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="标签ID列表"
    )
    file_type = serializers.CharField(max_length=50, required=False, help_text="文件类型")
    uploaded_by = serializers.CharField(max_length=150, required=False, help_text="上传用户")
    date_from = serializers.DateTimeField(required=False, help_text="开始日期")
    date_to = serializers.DateTimeField(required=False, help_text="结束日期")
    file_size_min = serializers.IntegerField(min_value=0, required=False, help_text="最小文件大小")
    file_size_max = serializers.IntegerField(min_value=0, required=False, help_text="最大文件大小")
    sort_by = serializers.ChoiceField(
        choices=[
            ('created_at', '创建时间'),
            ('updated_at', '更新时间'),
            ('view_count', '查看次数'),
            ('download_count', '下载次数'),
            ('file_size', '文件大小'),
        ],
        default='created_at',
        help_text="排序方式"
    )
    page = serializers.IntegerField(min_value=1, default=1, help_text="页码")
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20, help_text="每页数量")