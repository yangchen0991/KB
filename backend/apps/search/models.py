"""
搜索引擎模型
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class SearchQuery(models.Model):
    """搜索查询记录"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_queries')
    query = models.CharField(_("查询内容"), max_length=500)
    filters = models.JSONField(_("过滤条件"), default=dict, blank=True)
    results_count = models.PositiveIntegerField(_("结果数量"), default=0)
    execution_time = models.FloatField(_("执行时间(秒)"), default=0.0)
    
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("搜索查询")
        verbose_name_plural = _("搜索查询")
        db_table = "kb_search_queries"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['query']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.query}"


class SearchIndex(models.Model):
    """搜索索引状态"""
    
    STATUS_CHOICES = [
        ('pending', '待索引'),
        ('indexing', '索引中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]
    
    document = models.OneToOneField(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='search_index'
    )
    status = models.CharField(_("状态"), max_length=20, choices=STATUS_CHOICES, default='pending')
    indexed_content = models.TextField(_("索引内容"), blank=True)
    keywords = models.TextField(_("关键词"), blank=True)
    
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)
    
    class Meta:
        verbose_name = _("搜索索引")
        verbose_name_plural = _("搜索索引")
        db_table = "kb_search_indexes"
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['updated_at']),
        ]
    
    def __str__(self):
        return f"索引: {self.document.title}"


class PopularSearch(models.Model):
    """热门搜索"""
    
    query = models.CharField(_("查询内容"), max_length=200, unique=True)
    search_count = models.PositiveIntegerField(_("搜索次数"), default=1)
    last_searched = models.DateTimeField(_("最后搜索时间"), auto_now=True)
    
    class Meta:
        verbose_name = _("热门搜索")
        verbose_name_plural = _("热门搜索")
        db_table = "kb_popular_searches"
        ordering = ["-search_count", "-last_searched"]
    
    def __str__(self):
        return f"{self.query} ({self.search_count}次)"