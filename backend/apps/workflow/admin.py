import json

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import (
    NodeExecution,
    WorkflowExecution,
    WorkflowSchedule,
    WorkflowTemplate,
    WorkflowVariable,
)


@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "version",
        "status",
        "execution_count",
        "success_rate",
        "created_by",
        "created_at",
    ]
    list_filter = ["status", "created_at", "updated_at"]
    search_fields = ["name", "description"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "execution_count",
        "success_count",
    ]

    fieldsets = (
        ("基本信息", {"fields": ("name", "description", "version", "status")}),
        ("工作流定义", {"fields": ("definition",), "classes": ("wide",)}),
        (
            "统计信息",
            {"fields": ("execution_count", "success_count"), "classes": ("collapse",)},
        ),
        (
            "元数据",
            {
                "fields": ("id", "created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def success_rate(self, obj):
        return f"{obj.success_rate}%"

    success_rate.short_description = "成功率"


@admin.register(WorkflowExecution)
class WorkflowExecutionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "template_name",
        "status",
        "priority",
        "created_by",
        "created_at",
        "duration_display",
    ]
    list_filter = ["status", "priority", "created_at"]
    search_fields = ["template__name", "created_by__username"]
    readonly_fields = [
        "id",
        "created_at",
        "started_at",
        "completed_at",
        "output_data",
        "context",
        "duration_display",
    ]

    fieldsets = (
        ("基本信息", {"fields": ("template", "status", "priority")}),
        (
            "执行数据",
            {"fields": ("input_data", "output_data", "context"), "classes": ("wide",)},
        ),
        (
            "时间信息",
            {
                "fields": (
                    "created_at",
                    "started_at",
                    "completed_at",
                    "duration_display",
                )
            },
        ),
        (
            "错误信息",
            {
                "fields": ("error_message", "retry_count", "max_retries"),
                "classes": ("collapse",),
            },
        ),
        ("元数据", {"fields": ("id", "created_by"), "classes": ("collapse",)}),
    )

    def template_name(self, obj):
        return obj.template.name

    template_name.short_description = "工作流模板"

    def duration_display(self, obj):
        if obj.duration:
            return str(obj.duration)
        return "-"

    duration_display.short_description = "执行时长"


@admin.register(NodeExecution)
class NodeExecutionAdmin(admin.ModelAdmin):
    list_display = [
        "node_name",
        "node_type",
        "status",
        "workflow_execution",
        "started_at",
        "duration_display",
    ]
    list_filter = ["status", "node_type", "started_at"]
    search_fields = ["node_name", "node_id", "workflow_execution__template__name"]
    readonly_fields = [
        "id",
        "started_at",
        "completed_at",
        "duration_display",
        "output_data",
        "error_message",
    ]

    fieldsets = (
        (
            "节点信息",
            {
                "fields": (
                    "workflow_execution",
                    "node_id",
                    "node_type",
                    "node_name",
                    "status",
                )
            },
        ),
        ("执行数据", {"fields": ("input_data", "output_data"), "classes": ("wide",)}),
        ("时间信息", {"fields": ("started_at", "completed_at", "duration_display")}),
        (
            "错误信息",
            {"fields": ("error_message", "retry_count"), "classes": ("collapse",)},
        ),
    )

    def duration_display(self, obj):
        if obj.duration:
            return str(obj.duration)
        return "-"

    duration_display.short_description = "执行时长"


@admin.register(WorkflowSchedule)
class WorkflowScheduleAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "template",
        "schedule_type",
        "status",
        "last_run_at",
        "next_run_at",
        "execution_count",
    ]
    list_filter = ["schedule_type", "status", "created_at"]
    search_fields = ["name", "template__name"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "last_run_at",
        "next_run_at",
        "execution_count",
    ]

    fieldsets = (
        ("基本信息", {"fields": ("name", "template", "status")}),
        (
            "调度配置",
            {"fields": ("schedule_type", "schedule_config"), "classes": ("wide",)},
        ),
        ("执行配置", {"fields": ("input_data", "priority")}),
        (
            "执行信息",
            {
                "fields": ("last_run_at", "next_run_at", "execution_count"),
                "classes": ("collapse",),
            },
        ),
        (
            "元数据",
            {
                "fields": ("id", "created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(WorkflowVariable)
class WorkflowVariableAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "scope",
        "data_type",
        "template",
        "is_required",
        "is_encrypted",
        "created_by",
    ]
    list_filter = ["scope", "data_type", "is_required", "is_encrypted"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        ("基本信息", {"fields": ("name", "description", "scope", "data_type")}),
        ("变量值", {"fields": ("value", "default_value"), "classes": ("wide",)}),
        ("关联对象", {"fields": ("template", "execution")}),
        ("配置", {"fields": ("is_required", "is_encrypted")}),
        (
            "元数据",
            {
                "fields": ("id", "created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
