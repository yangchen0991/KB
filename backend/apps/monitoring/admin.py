"""
监控系统管理界面
"""

from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    AlertInstance,
    AlertRule,
    ApplicationMetrics,
    Dashboard,
    MetricData,
    MetricDefinition,
    SystemMetrics,
)


@admin.register(MetricDefinition)
class MetricDefinitionAdmin(admin.ModelAdmin):
    """指标定义管理"""

    list_display = [
        "name",
        "metric_type",
        "category",
        "prometheus_name",
        "is_enabled",
        "collection_interval",
        "retention_days",
        "created_by",
        "created_at",
    ]
    list_filter = ["metric_type", "category", "is_enabled", "created_at"]
    search_fields = ["name", "prometheus_name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        ("基本信息", {"fields": ("name", "description", "metric_type", "category")}),
        ("Prometheus配置", {"fields": ("prometheus_name", "labels", "help_text")}),
        (
            "采集配置",
            {"fields": ("collection_interval", "is_enabled", "retention_days")},
        ),
        (
            "元数据",
            {
                "fields": ("id", "created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MetricData)
class MetricDataAdmin(admin.ModelAdmin):
    """指标数据管理"""

    list_display = ["metric_definition", "timestamp", "value", "instance", "job"]
    list_filter = ["metric_definition", "timestamp", "instance", "job"]
    search_fields = ["metric_definition__name", "instance", "job"]
    readonly_fields = ["id"]
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        return False  # 指标数据由系统自动创建

    def has_change_permission(self, request, obj=None):
        return False  # 指标数据不允许修改


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    """告警规则管理"""

    list_display = [
        "name",
        "metric_definition",
        "severity",
        "status",
        "operator",
        "threshold",
        "total_alerts",
        "last_alert_at",
        "created_by",
    ]
    list_filter = ["severity", "status", "metric_definition", "created_at"]
    search_fields = ["name", "description", "metric_definition__name"]
    readonly_fields = [
        "id",
        "total_alerts",
        "last_alert_at",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        ("基本信息", {"fields": ("name", "description", "metric_definition")}),
        ("规则配置", {"fields": ("operator", "threshold", "duration")}),
        ("告警配置", {"fields": ("severity", "status")}),
        ("通知配置", {"fields": ("notification_channels", "notification_template")}),
        ("抑制配置", {"fields": ("silence_duration", "max_alerts_per_hour")}),
        (
            "统计信息",
            {"fields": ("total_alerts", "last_alert_at"), "classes": ("collapse",)},
        ),
        (
            "元数据",
            {
                "fields": ("id", "created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    actions = ["activate_rules", "deactivate_rules"]

    def activate_rules(self, request, queryset):
        """批量激活告警规则"""
        updated = queryset.update(status="active")
        self.message_user(request, f"成功激活 {updated} 个告警规则")

    activate_rules.short_description = "激活选中的告警规则"

    def deactivate_rules(self, request, queryset):
        """批量停用告警规则"""
        updated = queryset.update(status="inactive")
        self.message_user(request, f"成功停用 {updated} 个告警规则")

    deactivate_rules.short_description = "停用选中的告警规则"


@admin.register(AlertInstance)
class AlertInstanceAdmin(admin.ModelAdmin):
    """告警实例管理"""

    list_display = [
        "alert_rule",
        "status",
        "severity_display",
        "trigger_value",
        "started_at",
        "duration_display",
        "notification_count",
    ]
    list_filter = ["status", "alert_rule__severity", "started_at"]
    search_fields = ["alert_rule__name", "message"]
    readonly_fields = [
        "id",
        "duration_display",
        "started_at",
        "resolved_at",
        "notifications_sent",
        "notification_count",
    ]
    date_hierarchy = "started_at"

    fieldsets = (
        ("告警信息", {"fields": ("alert_rule", "status", "message")}),
        ("时间信息", {"fields": ("started_at", "resolved_at", "duration_display")}),
        ("触发数据", {"fields": ("trigger_value", "trigger_labels")}),
        (
            "通知状态",
            {
                "fields": ("notifications_sent", "notification_count"),
                "classes": ("collapse",),
            },
        ),
    )

    def severity_display(self, obj):
        """显示严重程度"""
        severity_colors = {
            "info": "blue",
            "warning": "orange",
            "critical": "red",
            "fatal": "darkred",
        }
        color = severity_colors.get(obj.alert_rule.severity, "gray")
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.alert_rule.get_severity_display(),
        )

    severity_display.short_description = "严重程度"

    def duration_display(self, obj):
        """显示持续时间"""
        duration = obj.duration
        if duration.total_seconds() < 60:
            return f"{int(duration.total_seconds())}秒"
        elif duration.total_seconds() < 3600:
            return f"{int(duration.total_seconds() / 60)}分钟"
        else:
            return f"{duration.total_seconds() / 3600:.1f}小时"

    duration_display.short_description = "持续时间"

    def has_add_permission(self, request):
        return False  # 告警实例由系统自动创建

    actions = ["resolve_alerts"]

    def resolve_alerts(self, request, queryset):
        """批量解决告警"""
        resolved_count = 0
        for alert in queryset.filter(status="firing"):
            alert.resolve()
            resolved_count += 1
        self.message_user(request, f"成功解决 {resolved_count} 个告警")

    resolve_alerts.short_description = "解决选中的告警"


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    """仪表板管理"""

    list_display = [
        "name",
        "is_public",
        "view_count",
        "last_viewed_at",
        "created_by",
        "created_at",
    ]
    list_filter = ["is_public", "created_at", "last_viewed_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "view_count", "last_viewed_at", "created_at", "updated_at"]
    filter_horizontal = ["allowed_users"]

    fieldsets = (
        ("基本信息", {"fields": ("name", "description")}),
        ("配置", {"fields": ("layout", "panels")}),
        ("访问控制", {"fields": ("is_public", "allowed_users")}),
        (
            "统计信息",
            {"fields": ("view_count", "last_viewed_at"), "classes": ("collapse",)},
        ),
        (
            "元数据",
            {
                "fields": ("id", "created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SystemMetrics)
class SystemMetricsAdmin(admin.ModelAdmin):
    """系统指标管理"""

    list_display = [
        "timestamp",
        "cpu_usage_percent",
        "memory_usage_percent",
        "disk_usage_percent",
        "active_connections",
    ]
    list_filter = ["timestamp"]
    readonly_fields = ["id", "timestamp"]
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        return False  # 系统指标由系统自动创建

    def has_change_permission(self, request, obj=None):
        return False  # 系统指标不允许修改


@admin.register(ApplicationMetrics)
class ApplicationMetricsAdmin(admin.ModelAdmin):
    """应用指标管理"""

    list_display = [
        "timestamp",
        "active_users",
        "total_users",
        "total_documents",
        "search_requests_today",
        "workflow_executions_today",
    ]
    list_filter = ["timestamp"]
    readonly_fields = ["id", "timestamp"]
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        return False  # 应用指标由系统自动创建

    def has_change_permission(self, request, obj=None):
        return False  # 应用指标不允许修改
