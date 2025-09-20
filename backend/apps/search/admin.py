"""
搜索系统管理界面
"""

from django.contrib import admin

from .models import SearchQuery, PopularSearch, SearchIndex


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    """搜索查询管理"""

    list_display = ["user", "query", "results_count", "execution_time", "created_at"]
    list_filter = ["created_at", "results_count"]
    search_fields = ["query", "user__username"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


@admin.register(PopularSearch)
class PopularSearchAdmin(admin.ModelAdmin):
    """热门搜索管理"""

    list_display = ["query", "search_count", "last_searched"]
    list_filter = ["last_searched"]
    search_fields = ["query"]
    readonly_fields = ["last_searched"]
    ordering = ["-search_count", "-last_searched"]


@admin.register(SearchIndex)
class SearchIndexAdmin(admin.ModelAdmin):
    """搜索索引管理"""

    list_display = [
        "document",
        "status",
        "created_at",
        "updated_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["document__title"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"
    ordering = ["-updated_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("document")