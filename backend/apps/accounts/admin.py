"""
用户账户管理后台
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, UserActivity, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """用户管理"""

    list_display = [
        "username",
        "email",
        "full_name",
        "department",
        "position",
        "is_verified",
        "documents_uploaded",
        "last_activity",
        "is_active",
    ]
    list_filter = [
        "is_active",
        "is_staff",
        "is_verified",
        "can_upload",
        "can_classify",
        "can_manage_workflows",
        "department",
    ]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering = ["-date_joined"]

    fieldsets = BaseUserAdmin.fieldsets + (
        (_("扩展信息"), {"fields": ("phone", "avatar", "department", "position")}),
        (
            _("权限设置"),
            {
                "fields": (
                    "is_verified",
                    "can_upload",
                    "can_classify",
                    "can_manage_workflows",
                )
            },
        ),
        (
            _("统计信息"),
            {
                "fields": ("documents_uploaded", "last_activity"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ["last_activity", "documents_uploaded"]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """用户配置管理"""

    list_display = [
        "user",
        "theme",
        "language",
        "email_notifications",
        "push_notifications",
        "auto_ocr",
    ]
    list_filter = [
        "theme",
        "language",
        "email_notifications",
        "push_notifications",
        "auto_ocr",
    ]
    search_fields = ["user__username", "user__email"]

    fieldsets = [
        (_("用户"), {"fields": ["user"]}),
        (_("界面设置"), {"fields": ["theme", "language"]}),
        (_("通知设置"), {"fields": ["email_notifications", "push_notifications"]}),
        (_("工作偏好"), {"fields": ["default_classification", "auto_ocr"]}),
    ]


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """用户活动管理"""

    list_display = ["user", "action", "description", "ip_address", "created_at"]
    list_filter = ["action", "created_at"]
    search_fields = ["user__username", "user__email", "description"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]

    fieldsets = [
        (_("基本信息"), {"fields": ["user", "action", "description"]}),
        (
            _("技术信息"),
            {"fields": ["ip_address", "user_agent"], "classes": ("collapse",)},
        ),
        (
            _("关联对象"),
            {"fields": ["content_type", "object_id"], "classes": ("collapse",)},
        ),
        (_("时间信息"), {"fields": ["created_at"]}),
    ]
