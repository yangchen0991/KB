"""
自定义权限类
"""

from django.contrib.auth.models import Group
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    只有对象的所有者才能编辑，其他人只能读取
    """

    def has_object_permission(self, request, view, obj):
        # 读取权限对所有人开放
        if request.method in permissions.SAFE_METHODS:
            return True

        # 写入权限只给所有者
        return obj.created_by == request.user


class IsDocumentOwnerOrShared(permissions.BasePermission):
    """
    文档权限：所有者或被分享的用户可以访问
    """

    def has_object_permission(self, request, view, obj):
        # 检查是否是文档所有者
        if obj.created_by == request.user:
            return True

        # 检查是否被分享
        if hasattr(obj, "shares"):
            return obj.shares.filter(shared_with=request.user).exists()

        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    管理员可以进行所有操作，其他用户只能读取
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        return request.user.is_staff


class HasGroupPermission(permissions.BasePermission):
    """
    基于用户组的权限控制
    """

    def __init__(self, required_groups=None):
        self.required_groups = required_groups or []

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        user_groups = request.user.groups.values_list("name", flat=True)
        return any(group in user_groups for group in self.required_groups)


class CanManageWorkflows(permissions.BasePermission):
    """
    工作流管理权限
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # 超级用户和工作流管理员可以管理
        if request.user.is_superuser:
            return True

        return request.user.groups.filter(name="workflow_managers").exists()


class CanViewReports(permissions.BasePermission):
    """
    报告查看权限
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # 超级用户、管理员和报告查看者可以查看
        if request.user.is_superuser or request.user.is_staff:
            return True

        return request.user.groups.filter(
            name__in=["report_viewers", "managers"]
        ).exists()


class CanManageSystem(permissions.BasePermission):
    """
    系统管理权限
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # 只有超级用户和系统管理员可以管理系统
        if request.user.is_superuser:
            return True

        return request.user.groups.filter(name="system_admins").exists()
