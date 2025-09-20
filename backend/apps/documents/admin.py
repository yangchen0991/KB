"""
文档管理后台
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    Category,
    Document,
    DocumentActivity,
    DocumentComment,
    DocumentShare,
    DocumentVersion,
    Tag,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """分类管理"""

    list_display = [
        "name",
        "parent",
        "color_display",
        "auto_classify",
        "document_count",
        "created_at",
    ]
    list_filter = ["auto_classify", "parent", "created_at"]
    search_fields = ["name", "description"]
    ordering = ["name"]

    fieldsets = [
        (_("基本信息"), {"fields": ["name", "description", "parent"]}),
        (_("显示设置"), {"fields": ["color", "icon"]}),
        (_("自动分类"), {"fields": ["auto_classify", "keywords"]}),
    ]

    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 2px 8px; color: white; border-radius: 3px;">{}</span>',
            obj.color,
            obj.color,
        )

    color_display.short_description = "颜色"

    def document_count(self, obj):
        return obj.documents.count()

    document_count.short_description = "文档数量"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """标签管理"""

    list_display = ["name", "color_display", "document_count", "created_at"]
    search_fields = ["name"]
    ordering = ["name"]

    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 2px 8px; color: white; border-radius: 3px;">{}</span>',
            obj.color,
            obj.color,
        )

    color_display.short_description = "颜色"

    def document_count(self, obj):
        return obj.documents.count()

    document_count.short_description = "文档数量"


class DocumentVersionInline(admin.TabularInline):
    """文档版本内联"""

    model = DocumentVersion
    extra = 0
    readonly_fields = ["created_at"]


class DocumentShareInline(admin.TabularInline):
    """文档分享内联"""

    model = DocumentShare
    extra = 0
    readonly_fields = ["created_at"]


class DocumentCommentInline(admin.TabularInline):
    """文档评论内联"""

    model = DocumentComment
    extra = 0
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """文档管理"""

    list_display = [
        "title",
        "category",
        "uploaded_by",
        "status",
        "file_type",
        "file_size_human",
        "view_count",
        "download_count",
        "created_at",
    ]
    list_filter = ["status", "file_type", "category", "is_public", "created_at"]
    search_fields = ["title", "description", "ocr_text"]
    readonly_fields = [
        "file_size",
        "file_type",
        "ocr_confidence",
        "view_count",
        "download_count",
        "created_at",
        "updated_at",
    ]
    filter_horizontal = ["tags", "shared_with"]

    fieldsets = [
        (_("基本信息"), {"fields": ["title", "description", "file", "uploaded_by"]}),
        (_("分类和标签"), {"fields": ["category", "tags"]}),
        (_("处理状态"), {"fields": ["status", "processing_progress"]}),
        (
            _("OCR信息"),
            {
                "fields": ["ocr_text", "ocr_confidence", "ocr_language"],
                "classes": ["collapse"],
            },
        ),
        (
            _("文件信息"),
            {
                "fields": [
                    "file_size",
                    "file_type",
                    "thumbnail",
                    "page_count",
                    "metadata",
                ],
                "classes": ["collapse"],
            },
        ),
        (_("访问控制"), {"fields": ["is_public", "shared_with"]}),
        (
            _("统计信息"),
            {
                "fields": ["view_count", "download_count", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    inlines = [DocumentVersionInline, DocumentShareInline, DocumentCommentInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category", "uploaded_by")


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    """文档版本管理"""

    list_display = ["document", "version_number", "uploaded_by", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["document__title", "comment"]
    readonly_fields = ["created_at"]


@admin.register(DocumentShare)
class DocumentShareAdmin(admin.ModelAdmin):
    """文档分享管理"""

    list_display = ["document", "shared_by", "shared_with", "permission", "created_at"]
    list_filter = ["permission", "created_at"]
    search_fields = ["document__title", "shared_by__username", "shared_with__username"]
    readonly_fields = ["created_at"]


@admin.register(DocumentComment)
class DocumentCommentAdmin(admin.ModelAdmin):
    """文档评论管理"""

    list_display = ["document", "user", "content_preview", "parent", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["document__title", "user__username", "content"]
    readonly_fields = ["created_at", "updated_at"]

    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    content_preview.short_description = "评论内容"


@admin.register(DocumentActivity)
class DocumentActivityAdmin(admin.ModelAdmin):
    """文档活动管理"""

    list_display = ["document", "user", "action", "description", "created_at"]
    list_filter = ["action", "created_at"]
    search_fields = ["document__title", "user__username", "description"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]
