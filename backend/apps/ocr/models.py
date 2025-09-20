"""
OCR识别模型
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class OCRTask(models.Model):
    """OCR识别任务"""
    
    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]
    
    PROVIDER_CHOICES = [
        ('tesseract', 'Tesseract'),
        ('baidu', '百度OCR'),
        ('tencent', '腾讯OCR'),
        ('aliyun', '阿里云OCR'),
        ('azure', 'Azure OCR'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='ocr_tasks',
        verbose_name=_('文档')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('用户')
    )
    
    # 任务信息
    status = models.CharField(
        _('状态'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    provider = models.CharField(
        _('OCR提供商'),
        max_length=20,
        choices=PROVIDER_CHOICES,
        default='tesseract'
    )
    
    # 识别结果
    extracted_text = models.TextField(_('识别文本'), blank=True)
    confidence_score = models.FloatField(_('置信度'), null=True, blank=True)
    language = models.CharField(_('语言'), max_length=10, default='zh-cn')
    
    # 处理信息
    processing_time = models.FloatField(_('处理时间(秒)'), null=True, blank=True)
    error_message = models.TextField(_('错误信息'), blank=True)
    
    # 时间戳
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    started_at = models.DateTimeField(_('开始时间'), null=True, blank=True)
    completed_at = models.DateTimeField(_('完成时间'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('OCR任务')
        verbose_name_plural = _('OCR任务')
        db_table = 'kb_ocr_tasks'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'OCR任务 - {self.document.title} ({self.status})'


class OCRResult(models.Model):
    """OCR识别结果详情"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.OneToOneField(
        OCRTask,
        on_delete=models.CASCADE,
        related_name='result',
        verbose_name=_('OCR任务')
    )
    
    # 详细结果
    raw_result = models.JSONField(_('原始结果'), default=dict)
    structured_data = models.JSONField(_('结构化数据'), default=dict)
    
    # 文本块信息
    text_blocks = models.JSONField(_('文本块'), default=list)
    word_count = models.IntegerField(_('字数'), default=0)
    line_count = models.IntegerField(_('行数'), default=0)
    
    # 质量评估
    quality_score = models.FloatField(_('质量评分'), null=True, blank=True)
    blur_score = models.FloatField(_('模糊度'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('OCR结果')
        verbose_name_plural = _('OCR结果')
        db_table = 'kb_ocr_results'
    
    def __str__(self):
        return f'OCR结果 - {self.task.document.title}'