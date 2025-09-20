#!/usr/bin/env python
"""
数据库初始化脚本
"""
import os
import sys

import django
from django.core.management import execute_from_command_line

# 设置Django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "knowledge_base.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from apps.accounts.models import UserProfile
from apps.classification.models import Category, ClassificationModel
from apps.monitoring.models import AlertRule, HealthCheck

User = get_user_model()


def create_superuser():
    """创建超级用户"""
    if not User.objects.filter(username="admin").exists():
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin123",
            first_name="系统",
            last_name="管理员",
        )

        # 创建用户配置
        UserProfile.objects.create(
            user=admin, department="IT部门", position="系统管理员", phone="13800138000"
        )

        print("✓ 创建超级用户: admin/admin123")
    else:
        print("✓ 超级用户已存在")


def create_groups():
    """创建用户组"""
    groups_data = [
        {
            "name": "system_admins",
            "display_name": "系统管理员",
            "permissions": ["add_user", "change_user", "delete_user", "view_user"],
        },
        {
            "name": "workflow_managers",
            "display_name": "工作流管理员",
            "permissions": [
                "add_workflowtemplate",
                "change_workflowtemplate",
                "delete_workflowtemplate",
            ],
        },
        {
            "name": "report_viewers",
            "display_name": "报告查看者",
            "permissions": ["view_performancereport", "view_systemmetric"],
        },
        {
            "name": "document_managers",
            "display_name": "文档管理员",
            "permissions": [
                "add_document",
                "change_document",
                "delete_document",
                "view_document",
            ],
        },
        {
            "name": "regular_users",
            "display_name": "普通用户",
            "permissions": ["view_document", "add_document"],
        },
    ]

    for group_data in groups_data:
        group, created = Group.objects.get_or_create(name=group_data["name"])
        if created:
            print(f"✓ 创建用户组: {group_data['display_name']}")
        else:
            print(f"✓ 用户组已存在: {group_data['display_name']}")


def create_default_categories():
    """创建默认分类"""
    categories_data = [
        {"name": "技术文档", "description": "技术相关的文档资料", "color": "#007bff"},
        {"name": "管理制度", "description": "公司管理制度文件", "color": "#28a745"},
        {"name": "培训资料", "description": "员工培训相关资料", "color": "#ffc107"},
        {"name": "项目文档", "description": "项目相关文档", "color": "#dc3545"},
        {"name": "财务报表", "description": "财务相关报表", "color": "#6f42c1"},
        {"name": "合同协议", "description": "各类合同协议", "color": "#fd7e14"},
        {"name": "其他", "description": "其他类型文档", "color": "#6c757d"},
    ]

    admin_user = User.objects.get(username="admin")

    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data["name"],
            defaults={
                "description": cat_data["description"],
                "color": cat_data["color"],
                "created_by": admin_user,
            },
        )
        if created:
            print(f"✓ 创建分类: {cat_data['name']}")
        else:
            print(f"✓ 分类已存在: {cat_data['name']}")


def create_default_health_checks():
    """创建默认健康检查"""
    health_checks_data = [
        {
            "name": "数据库连接",
            "description": "检查数据库连接状态",
            "check_type": "database",
            "check_config": {"timeout": 5},
            "check_interval": 60,
        },
        {
            "name": "Redis连接",
            "description": "检查Redis连接状态",
            "check_type": "redis",
            "check_config": {"timeout": 5},
            "check_interval": 60,
        },
        {
            "name": "Elasticsearch连接",
            "description": "检查Elasticsearch连接状态",
            "check_type": "elasticsearch",
            "check_config": {"timeout": 10},
            "check_interval": 120,
        },
        {
            "name": "Celery队列",
            "description": "检查Celery队列状态",
            "check_type": "celery",
            "check_config": {"max_queue_size": 1000},
            "check_interval": 300,
        },
    ]

    for hc_data in health_checks_data:
        health_check, created = HealthCheck.objects.get_or_create(
            name=hc_data["name"], defaults=hc_data
        )
        if created:
            print(f"✓ 创建健康检查: {hc_data['name']}")
        else:
            print(f"✓ 健康检查已存在: {hc_data['name']}")


def create_default_alert_rules():
    """创建默认告警规则"""
    admin_user = User.objects.get(username="admin")

    alert_rules_data = [
        {
            "name": "CPU使用率过高",
            "description": "CPU使用率超过80%时触发告警",
            "metric_type": "cpu_usage",
            "condition": "gt",
            "threshold": 80.0,
            "severity": "high",
            "notification_channels": ["email", "webhook"],
        },
        {
            "name": "内存使用率过高",
            "description": "内存使用率超过85%时触发告警",
            "metric_type": "memory_usage",
            "condition": "gt",
            "threshold": 85.0,
            "severity": "high",
            "notification_channels": ["email"],
        },
        {
            "name": "磁盘使用率过高",
            "description": "磁盘使用率超过90%时触发告警",
            "metric_type": "disk_usage",
            "condition": "gt",
            "threshold": 90.0,
            "severity": "critical",
            "notification_channels": ["email", "sms", "webhook"],
        },
        {
            "name": "错误率过高",
            "description": "错误率超过5%时触发告警",
            "metric_type": "error_rate",
            "condition": "gt",
            "threshold": 5.0,
            "severity": "medium",
            "notification_channels": ["email"],
        },
    ]

    for rule_data in alert_rules_data:
        alert_rule, created = AlertRule.objects.get_or_create(
            name=rule_data["name"], defaults={**rule_data, "created_by": admin_user}
        )
        if created:
            print(f"✓ 创建告警规则: {rule_data['name']}")
            # 添加管理员为通知用户
            alert_rule.notification_users.add(admin_user)
        else:
            print(f"✓ 告警规则已存在: {rule_data['name']}")


def main():
    """主函数"""
    print("开始初始化数据库...")

    # 执行数据库迁移
    print("\n1. 执行数据库迁移...")
    execute_from_command_line(["manage.py", "makemigrations"])
    execute_from_command_line(["manage.py", "migrate"])

    # 创建基础数据
    print("\n2. 创建基础数据...")
    create_superuser()
    create_groups()
    create_default_categories()
    create_default_health_checks()
    create_default_alert_rules()

    # 收集静态文件
    print("\n3. 收集静态文件...")
    execute_from_command_line(["manage.py", "collectstatic", "--noinput"])

    print("\n✅ 数据库初始化完成！")
    print("\n登录信息:")
    print("  用户名: admin")
    print("  密码: admin123")
    print("  管理后台: http://localhost:8000/admin/")
    print("  API文档: http://localhost:8000/api/docs/")


if __name__ == "__main__":
    main()
