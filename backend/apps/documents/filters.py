"""
文档过滤器
"""

import django_filters
from django.db.models import Q
from .models import Document, Category, Tag


class DocumentFilter(django_filters.FilterSet):
    """文档过滤器"""
    
    # 基本过滤
    title = django_filters.CharFilter(lookup_expr='icontains', help_text="标题包含")
    description = django_filters.CharFilter(lookup_expr='icontains', help_text="描述包含")
    
    # 分类过滤
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        help_text="分类"
    )
    category_name = django_filters.CharFilter(
        field_name='category__name',
        lookup_expr='icontains',
        help_text="分类名称包含"
    )
    
    # 标签过滤
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        help_text="标签（多选）"
    )
    
    # 文件类型过滤
    file_type = django_filters.ChoiceFilter(
        choices=[
            ('pdf', 'PDF'),
            ('doc', 'Word文档'),
            ('docx', 'Word文档'),
            ('txt', '文本文件'),
            ('jpg', '图片'),
            ('jpeg', '图片'),
            ('png', '图片'),
            ('tiff', '图片'),
        ],
        help_text="文件类型"
    )
    
    # 文件大小过滤
    file_size_min = django_filters.NumberFilter(
        field_name='file_size',
        lookup_expr='gte',
        help_text="最小文件大小（字节）"
    )
    file_size_max = django_filters.NumberFilter(
        field_name='file_size',
        lookup_expr='lte',
        help_text="最大文件大小（字节）"
    )
    
    # 状态过滤
    status = django_filters.ChoiceFilter(
        choices=Document.STATUS_CHOICES,
        help_text="处理状态"
    )
    
    # 用户过滤
    uploaded_by = django_filters.CharFilter(
        field_name='uploaded_by__username',
        lookup_expr='icontains',
        help_text="上传用户"
    )
    
    # 时间范围过滤
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        help_text="创建时间晚于"
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        help_text="创建时间早于"
    )
    
    # 访问权限过滤
    is_public = django_filters.BooleanFilter(help_text="是否公开")
    
    # 统计数据过滤
    view_count_min = django_filters.NumberFilter(
        field_name='view_count',
        lookup_expr='gte',
        help_text="最小查看次数"
    )
    download_count_min = django_filters.NumberFilter(
        field_name='download_count',
        lookup_expr='gte',
        help_text="最小下载次数"
    )
    
    # OCR相关过滤
    has_ocr_text = django_filters.BooleanFilter(
        method='filter_has_ocr_text',
        help_text="是否有OCR文本"
    )
    ocr_confidence_min = django_filters.NumberFilter(
        field_name='ocr_confidence',
        lookup_expr='gte',
        help_text="最小OCR置信度"
    )
    
    # 全文搜索
    search = django_filters.CharFilter(
        method='filter_search',
        help_text="全文搜索（标题、描述、OCR文本）"
    )
    
    class Meta:
        model = Document
        fields = []
    
    def filter_has_ocr_text(self, queryset, name, value):
        """过滤是否有OCR文本"""
        if value:
            return queryset.exclude(Q(ocr_text='') | Q(ocr_text__isnull=True))
        else:
            return queryset.filter(Q(ocr_text='') | Q(ocr_text__isnull=True))
    
    def filter_search(self, queryset, name, value):
        """全文搜索过滤"""
        if not value:
            return queryset
        
        # 构建搜索查询
        search_query = Q()
        
        # 分词搜索
        terms = value.split()
        for term in terms:
            term_query = (
                Q(title__icontains=term) |
                Q(description__icontains=term) |
                Q(ocr_text__icontains=term) |
                Q(tags__name__icontains=term) |
                Q(category__name__icontains=term)
            )
            search_query &= term_query
        
        return queryset.filter(search_query).distinct()


class CategoryFilter(django_filters.FilterSet):
    """分类过滤器"""
    
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    parent = django_filters.ModelChoiceFilter(queryset=Category.objects.all())
    auto_classify = django_filters.BooleanFilter()
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'parent', 'auto_classify']


class TagFilter(django_filters.FilterSet):
    """标签过滤器"""
    
    name = django_filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Tag
        fields = ['name']