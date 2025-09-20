"""
用户账户模型
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """扩展用户模型"""

    # 重写email字段以确保唯一性
    email = models.EmailField(_("邮箱地址"), unique=True)

    # 添加related_name以避免冲突
    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name=_("groups"),
        blank=True,
        help_text=_("The groups this user belongs to."),
        related_name="kb_user_set",
        related_query_name="kb_user",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_name="kb_user_set",
        related_query_name="kb_user",
    )
    phone = models.CharField(_("手机号码"), max_length=20, blank=True)
    avatar = models.ImageField(_("头像"), upload_to="avatars/", blank=True, null=True)
    department = models.CharField(_("部门"), max_length=100, blank=True)
    position = models.CharField(_("职位"), max_length=100, blank=True)

    # 权限相关
    is_verified = models.BooleanField(_("已验证"), default=False)
    can_upload = models.BooleanField(_("可上传文档"), default=True)
    can_classify = models.BooleanField(_("可分类文档"), default=False)
    can_manage_workflows = models.BooleanField(_("可管理工作流"), default=False)

    # 统计信息
    documents_uploaded = models.PositiveIntegerField(_("上传文档数"), default=0)
    last_activity = models.DateTimeField(_("最后活动时间"), auto_now=True)

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = _("用户")
        verbose_name_plural = _("用户")
        db_table = "kb_users"

    def __str__(self):
        return f"{self.username} ({self.email})"

    @property
    def full_name(self):
        """获取全名"""
        return f"{self.first_name} {self.last_name}".strip() or self.username


class UserProfile(models.Model):
    """用户配置文件"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # 界面设置
    theme = models.CharField(
        _("主题"),
        max_length=20,
        default="light",
        choices=[("light", "浅色"), ("dark", "深色")],
    )
    language = models.CharField(
        _("语言"),
        max_length=10,
        default="zh-hans",
        choices=[("zh-hans", "简体中文"), ("en", "English")],
    )

    # 通知设置
    email_notifications = models.BooleanField(_("邮件通知"), default=True)
    push_notifications = models.BooleanField(_("推送通知"), default=True)

    # 工作偏好
    default_classification = models.CharField(_("默认分类"), max_length=100, blank=True)
    auto_ocr = models.BooleanField(_("自动OCR"), default=True)

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("用户配置")
        verbose_name_plural = _("用户配置")
        db_table = "kb_user_profiles"

    def __str__(self):
        return f"{self.user.username} 的配置"


class UserActivity(models.Model):
    """用户活动记录"""

    ACTION_CHOICES = [
        ("login", "登录"),
        ("logout", "登出"),
        ("upload", "上传文档"),
        ("download", "下载文档"),
        ("search", "搜索"),
        ("classify", "分类"),
        ("delete", "删除"),
        ("share", "分享"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
    action = models.CharField(_("操作"), max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(_("描述"), blank=True)
    ip_address = models.GenericIPAddressField(_("IP地址"), blank=True, null=True)
    user_agent = models.TextField(_("用户代理"), blank=True)

    # 关联对象
    content_type = models.ForeignKey(
        "contenttypes.ContentType", on_delete=models.CASCADE, blank=True, null=True
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)

    class Meta:
        verbose_name = _("用户活动")
        verbose_name_plural = _("用户活动")
        db_table = "kb_user_activities"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()}"
