"""
文档管理模型 - 增强安全检查
"""

import hashlib
import os
import uuid

try:
    import magic
except ImportError:
    magic = None
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


def document_upload_path(instance, filename):
    """文档上传路径"""
    from datetime import datetime
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    
    # 使用当前时间，因为created_at在创建时可能为None
    now = datetime.now()
    return os.path.join(
        "documents",
        str(now.year),
        str(now.month),
        filename,
    )


def thumbnail_upload_path(instance, filename):
    """缩略图上传路径"""
    from datetime import datetime
    ext = filename.split(".")[-1]
    filename = f"thumb_{uuid.uuid4()}.{ext}"
    
    # 使用当前时间，因为created_at在创建时可能为None
    now = datetime.now()
    return os.path.join(
        "thumbnails",
        str(now.year),
        str(now.month),
        filename,
    )


class Category(models.Model):
    """文档分类"""

    name = models.CharField(_("分类名称"), max_length=100, unique=True)
    description = models.TextField(_("描述"), blank=True)
    color = models.CharField(_("颜色"), max_length=7, default="#007bff")
    icon = models.CharField(_("图标"), max_length=50, blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="children", blank=True, null=True
    )

    # 机器学习相关
    auto_classify = models.BooleanField(_("自动分类"), default=False)
    keywords = models.TextField(_("关键词"), blank=True, help_text="用逗号分隔的关键词")

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("文档分类")
        verbose_name_plural = _("文档分类")
        db_table = "kb_categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def full_path(self):
        """获取完整路径"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name


class Tag(models.Model):
    """文档标签"""

    name = models.CharField(_("标签名称"), max_length=50, unique=True)
    color = models.CharField(_("颜色"), max_length=7, default="#6c757d")

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)

    class Meta:
        verbose_name = _("文档标签")
        verbose_name_plural = _("文档标签")
        db_table = "kb_tags"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Document(models.Model):
    """文档模型 - 增强安全检查"""

    STATUS_CHOICES = [
        ("pending", "待处理"),
        ("processing", "处理中"),
        ("completed", "已完成"),
        ("failed", "处理失败"),
    ]

    # 安全配置
    ALLOWED_FILE_TYPES = {
        "pdf": ["application/pdf"],
        "doc": ["application/msword"],
        "docx": [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ],
        "txt": ["text/plain"],
        "jpg": ["image/jpeg"],
        "jpeg": ["image/jpeg"],
        "png": ["image/png"],
        "tiff": ["image/tiff"],
    }
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    # 基本信息
    title = models.CharField(_("标题"), max_length=255)
    description = models.TextField(_("描述"), blank=True)
    file = models.FileField(
        _("文件"),
        upload_to=document_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    "pdf",
                    "doc",
                    "docx",
                    "txt",
                    "jpg",
                    "jpeg",
                    "png",
                    "tiff",
                ]
            )
        ],
    )
    file_size = models.PositiveIntegerField(_("文件大小"), default=0)
    file_type = models.CharField(_("文件类型"), max_length=50)
    file_hash = models.CharField(_("文件哈希"), max_length=64, blank=True)

    # 分类和标签
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="documents",
        blank=True,
        null=True,
    )
    tags = models.ManyToManyField(Tag, related_name="documents", blank=True)

    # 用户信息
    uploaded_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="uploaded_documents"
    )

    # 处理状态
    status = models.CharField(
        _("状态"), max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    processing_progress = models.PositiveIntegerField(_("处理进度"), default=0)

    # OCR 相关
    ocr_text = models.TextField(_("OCR文本"), blank=True)
    ocr_confidence = models.FloatField(_("OCR置信度"), default=0.0)
    ocr_language = models.CharField(_("OCR语言"), max_length=20, blank=True)

    # 缩略图和预览
    thumbnail = models.ImageField(
        _("缩略图"), upload_to=thumbnail_upload_path, blank=True, null=True
    )
    page_count = models.PositiveIntegerField(_("页数"), default=1)

    # 元数据
    metadata = models.JSONField(_("元数据"), default=dict, blank=True)

    # 访问控制
    is_public = models.BooleanField(_("公开"), default=False)
    shared_with = models.ManyToManyField(
        User, related_name="shared_documents", blank=True
    )

    # 统计信息
    view_count = models.PositiveIntegerField(_("查看次数"), default=0)
    download_count = models.PositiveIntegerField(_("下载次数"), default=0)

    # 时间信息
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("文档")
        verbose_name_plural = _("文档")
        db_table = "kb_documents"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["category"]),
            models.Index(fields=["uploaded_by"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        """文件安全验证"""
        if self.file:
            # 1. 文件大小检查
            if self.file.size > self.MAX_FILE_SIZE:
                raise ValidationError(
                    f"文件大小不能超过 {self.MAX_FILE_SIZE // (1024*1024)}MB"
                )

            # 2. 文件扩展名检查
            file_ext = self.file.name.split(".")[-1].lower()
            if file_ext not in self.ALLOWED_FILE_TYPES:
                raise ValidationError(f"不支持的文件类型: {file_ext}")

            # 3. 文件名安全检查
            import re

            if not re.match(r"^[a-zA-Z0-9._\-\u4e00-\u9fff\s]+$", self.file.name):
                raise ValidationError("文件名包含非法字符")

            # 4. MIME类型检查 (如果python-magic可用)
            try:
                file_content = self.file.read()
                self.file.seek(0)  # 重置文件指针

                if magic:
                    mime_type = magic.from_buffer(file_content, mime=True)
                    allowed_mimes = self.ALLOWED_FILE_TYPES[file_ext]

                    if mime_type not in allowed_mimes:
                        raise ValidationError(f"文件内容与扩展名不匹配: {mime_type}")

                # 5. 计算文件哈希
                self.file_hash = hashlib.sha256(file_content).hexdigest()

            except Exception as e:
                raise ValidationError(f"文件验证失败: {str(e)}")

    def save(self, *args, **kwargs):
        # 执行安全验证
        self.full_clean()

        if self.file:
            self.file_size = self.file.size
            self.file_type = self.file.name.split(".")[-1].lower()
        super().save(*args, **kwargs)

    @property
    def file_size_human(self):
        """人类可读的文件大小"""
        size = self.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class DocumentVersion(models.Model):
    """文档版本"""

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="versions"
    )
    version_number = models.PositiveIntegerField(_("版本号"))
    file = models.FileField(_("文件"), upload_to=document_upload_path)
    comment = models.TextField(_("版本说明"), blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)

    class Meta:
        verbose_name = _("文档版本")
        verbose_name_plural = _("文档版本")
        db_table = "kb_document_versions"
        unique_together = ["document", "version_number"]
        ordering = ["-version_number"]

    def __str__(self):
        return f"{self.document.title} v{self.version_number}"


class DocumentShare(models.Model):
    """文档分享"""

    PERMISSION_CHOICES = [
        ("view", "查看"),
        ("download", "下载"),
        ("edit", "编辑"),
    ]

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="shares"
    )
    shared_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="shared_documents_by_me"
    )
    shared_with = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="shared_documents_with_me"
    )
    permission = models.CharField(
        _("权限"), max_length=20, choices=PERMISSION_CHOICES, default="view"
    )

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)

    class Meta:
        verbose_name = _("文档分享")
        verbose_name_plural = _("文档分享")
        db_table = "kb_document_shares"
        unique_together = ["document", "shared_with"]

    def __str__(self):
        return f"{self.document.title} -> {self.shared_with.username}"


class DocumentComment(models.Model):
    """文档评论"""

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="comments"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(_("评论内容"))
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="replies", blank=True, null=True
    )

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("文档评论")
        verbose_name_plural = _("文档评论")
        db_table = "kb_document_comments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} 对 {self.document.title} 的评论"


class DocumentActivity(models.Model):
    """文档活动记录"""

    ACTION_CHOICES = [
        ("upload", "上传"),
        ("view", "查看"),
        ("download", "下载"),
        ("edit", "编辑"),
        ("delete", "删除"),
        ("share", "分享"),
        ("comment", "评论"),
    ]

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="activities"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(_("操作"), max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(_("描述"), blank=True)

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)

    class Meta:
        verbose_name = _("文档活动")
        verbose_name_plural = _("文档活动")
        db_table = "kb_document_activities"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} {self.get_action_display()} {self.document.title}"
