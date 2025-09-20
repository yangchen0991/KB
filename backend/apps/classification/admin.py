"""
文档分类管理后台
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    ClassificationLog,
    ClassificationModel,
    ClassificationRule,
    TrainingDataset,
    TrainingSample,
)


@admin.register(ClassificationModel)
class ClassificationModelAdmin(admin.ModelAdmin):
    """分类模型管理"""

    list_display = [
        "name",
        "version",
        "algorithm",
        "status",
        "is_active",
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "created_at",
    ]
    list_filter = ["status", "algorithm", "is_active", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = [
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "training_samples",
        "feature_count",
        "created_at",
        "updated_at",
    ]

    fieldsets = [
        (_("基本信息"), {"fields": ["name", "description", "version", "algorithm"]}),
        (_("模型文件"), {"fields": ["model_file", "vectorizer_file"]}),
        (_("训练参数"), {"fields": ["training_params"], "classes": ["collapse"]}),
        (
            _("性能指标"),
            {
                "fields": [
                    "accuracy",
                    "precision",
                    "recall",
                    "f1_score",
                    "training_samples",
                    "feature_count",
                ],
                "classes": ["collapse"],
            },
        ),
        (_("状态"), {"fields": ["status", "is_active"]}),
        (_("时间信息"), {"fields": ["created_at", "updated_at", "trained_at"]}),
    ]

    actions = ["activate_models", "deactivate_models"]

    def activate_models(self, request, queryset):
        # 先取消所有模型的激活状态
        ClassificationModel.objects.update(is_active=False)
        # 激活选中的模型（通常只选一个）
        updated = queryset.update(is_active=True)
        self.message_user(request, f"已激活 {updated} 个模型")

    activate_models.short_description = "激活选中的模型"

    def deactivate_models(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"已取消激活 {updated} 个模型")

    deactivate_models.short_description = "取消激活选中的模型"


class TrainingSampleInline(admin.TabularInline):
    """训练样本内联"""

    model = TrainingSample
    extra = 0
    readonly_fields = ["text_length", "created_at"]
    fields = ["text", "category", "is_validated", "text_length"]


@admin.register(TrainingDataset)
class TrainingDatasetAdmin(admin.ModelAdmin):
    """训练数据集管理"""

    list_display = [
        "name",
        "total_samples",
        "min_samples_per_category",
        "avg_text_length",
        "created_by",
        "created_at",
    ]
    list_filter = ["created_at"]
    search_fields = ["name", "description"]
    readonly_fields = [
        "total_samples",
        "category_distribution",
        "avg_text_length",
        "min_samples_per_category",
        "created_at",
        "updated_at",
    ]

    fieldsets = [
        (_("基本信息"), {"fields": ["name", "description", "created_by"]}),
        (
            _("数据统计"),
            {
                "fields": [
                    "total_samples",
                    "category_distribution",
                    "avg_text_length",
                    "min_samples_per_category",
                ],
                "classes": ["collapse"],
            },
        ),
        (_("时间信息"), {"fields": ["created_at", "updated_at"]}),
    ]

    inlines = [TrainingSampleInline]


@admin.register(TrainingSample)
class TrainingSampleAdmin(admin.ModelAdmin):
    """训练样本管理"""

    list_display = [
        "dataset",
        "category",
        "text_preview",
        "text_length",
        "is_validated",
        "created_at",
    ]
    list_filter = ["dataset", "category", "is_validated", "created_at"]
    search_fields = ["text"]
    readonly_fields = ["text_length", "created_at"]

    def text_preview(self, obj):
        return obj.text[:100] + "..." if len(obj.text) > 100 else obj.text

    text_preview.short_description = "文本预览"


@admin.register(ClassificationRule)
class ClassificationRuleAdmin(admin.ModelAdmin):
    """分类规则管理"""

    list_display = [
        "name",
        "rule_type",
        "target_category",
        "priority",
        "is_active",
        "match_count",
        "success_rate",
        "created_at",
    ]
    list_filter = ["rule_type", "target_category", "is_active", "created_at"]
    search_fields = ["name", "description", "pattern"]
    readonly_fields = ["match_count", "success_rate", "created_at", "updated_at"]

    fieldsets = [
        (_("基本信息"), {"fields": ["name", "description", "created_by"]}),
        (
            _("规则配置"),
            {"fields": ["rule_type", "pattern", "target_category", "priority"]},
        ),
        (_("状态"), {"fields": ["is_active"]}),
        (
            _("统计信息"),
            {"fields": ["match_count", "success_rate"], "classes": ["collapse"]},
        ),
        (_("时间信息"), {"fields": ["created_at", "updated_at"]}),
    ]


@admin.register(ClassificationLog)
class ClassificationLogAdmin(admin.ModelAdmin):
    """分类日志管理"""

    list_display = [
        "document",
        "predicted_category",
        "actual_category",
        "method",
        "confidence",
        "is_correct",
        "executed_at",
    ]
    list_filter = ["method", "is_correct", "executed_at", "predicted_category"]
    search_fields = ["document__title"]
    readonly_fields = ["executed_at"]

    fieldsets = [
        (_("文档信息"), {"fields": ["document"]}),
        (
            _("分类结果"),
            {"fields": ["predicted_category", "actual_category", "is_correct"]},
        ),
        (_("分类方法"), {"fields": ["method", "confidence", "model", "rule"]}),
        (_("执行信息"), {"fields": ["executed_by", "executed_at"]}),
        (_("元数据"), {"fields": ["metadata"], "classes": ["collapse"]}),
    ]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "document",
                "predicted_category",
                "actual_category",
                "model",
                "rule",
                "executed_by",
            )
        )
