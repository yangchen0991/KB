"""
监控系统序列化器
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    AlertInstance,
    AlertRule,
    ApplicationMetrics,
    Dashboard,
    MetricData,
    MetricDefinition,
    SystemMetrics,
)

User = get_user_model()


class MetricDefinitionSerializer(serializers.ModelSerializer):
    """指标定义序列化器"""

    created_by_name = serializers.CharField(source="created_by.email", read_only=True)
    metric_type_display = serializers.CharField(
        source="get_metric_type_display", read_only=True
    )
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )

    class Meta:
        model = MetricDefinition
        fields = [
            "id",
            "name",
            "description",
            "metric_type",
            "metric_type_display",
            "category",
            "category_display",
            "prometheus_name",
            "labels",
            "help_text",
            "collection_interval",
            "is_enabled",
            "retention_days",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def validate_prometheus_name(self, value):
        """验证Prometheus指标名称"""
        import re

        if not re.match(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$", value):
            raise serializers.ValidationError("Prometheus指标名称格式不正确")
        return value

    def validate_labels(self, value):
        """验证标签定义"""
        if not isinstance(value, list):
            raise serializers.ValidationError("标签定义必须是列表格式")

        for label in value:
            if not isinstance(label, dict) or "name" not in label:
                raise serializers.ValidationError("每个标签必须包含name字段")

        return value


class MetricDataSerializer(serializers.ModelSerializer):
    """指标数据序列化器"""

    metric_name = serializers.CharField(source="metric_definition.name", read_only=True)
    metric_type = serializers.CharField(
        source="metric_definition.metric_type", read_only=True
    )

    class Meta:
        model = MetricData
        fields = [
            "id",
            "metric_definition",
            "metric_name",
            "metric_type",
            "timestamp",
            "value",
            "labels",
            "instance",
            "job",
        ]
        read_only_fields = ["id"]


class AlertRuleSerializer(serializers.ModelSerializer):
    """告警规则序列化器"""

    created_by_name = serializers.CharField(source="created_by.email", read_only=True)
    metric_name = serializers.CharField(source="metric_definition.name", read_only=True)
    severity_display = serializers.CharField(
        source="get_severity_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    operator_display = serializers.CharField(
        source="get_operator_display", read_only=True
    )

    class Meta:
        model = AlertRule
        fields = [
            "id",
            "name",
            "description",
            "metric_definition",
            "metric_name",
            "operator",
            "operator_display",
            "threshold",
            "duration",
            "severity",
            "severity_display",
            "status",
            "status_display",
            "notification_channels",
            "notification_template",
            "silence_duration",
            "max_alerts_per_hour",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
            "total_alerts",
            "last_alert_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "created_at",
            "updated_at",
            "total_alerts",
            "last_alert_at",
        ]

    def validate_threshold(self, value):
        """验证阈值"""
        if not isinstance(value, (int, float)):
            raise serializers.ValidationError("阈值必须是数字")
        return value

    def validate_duration(self, value):
        """验证持续时间"""
        if value < 0:
            raise serializers.ValidationError("持续时间不能为负数")
        return value


class AlertInstanceSerializer(serializers.ModelSerializer):
    """告警实例序列化器"""

    rule_name = serializers.CharField(source="alert_rule.name", read_only=True)
    rule_severity = serializers.CharField(source="alert_rule.severity", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = AlertInstance
        fields = [
            "id",
            "alert_rule",
            "rule_name",
            "rule_severity",
            "status",
            "status_display",
            "message",
            "started_at",
            "resolved_at",
            "duration_seconds",
            "trigger_value",
            "trigger_labels",
            "notifications_sent",
            "notification_count",
        ]
        read_only_fields = ["id", "duration_seconds"]

    def get_duration_seconds(self, obj):
        """获取告警持续时间（秒）"""
        return obj.duration.total_seconds()


class DashboardSerializer(serializers.ModelSerializer):
    """仪表板序列化器"""

    created_by_name = serializers.CharField(source="created_by.email", read_only=True)
    allowed_users_names = serializers.SerializerMethodField()

    class Meta:
        model = Dashboard
        fields = [
            "id",
            "name",
            "description",
            "layout",
            "panels",
            "is_public",
            "allowed_users",
            "allowed_users_names",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
            "view_count",
            "last_viewed_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "created_at",
            "updated_at",
            "view_count",
            "last_viewed_at",
        ]

    def get_allowed_users_names(self, obj):
        """获取允许访问用户的名称列表"""
        return [user.email for user in obj.allowed_users.all()]

    def validate_layout(self, value):
        """验证布局配置"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("布局配置必须是字典格式")
        return value

    def validate_panels(self, value):
        """验证面板配置"""
        if not isinstance(value, list):
            raise serializers.ValidationError("面板配置必须是列表格式")

        for panel in value:
            if not isinstance(panel, dict) or "type" not in panel:
                raise serializers.ValidationError("每个面板必须包含type字段")

        return value


class SystemMetricsSerializer(serializers.ModelSerializer):
    """系统指标序列化器"""

    class Meta:
        model = SystemMetrics
        fields = [
            "id",
            "timestamp",
            "cpu_usage_percent",
            "cpu_load_1m",
            "cpu_load_5m",
            "cpu_load_15m",
            "memory_usage_percent",
            "memory_used_bytes",
            "memory_total_bytes",
            "disk_usage_percent",
            "disk_used_bytes",
            "disk_total_bytes",
            "network_bytes_sent",
            "network_bytes_recv",
            "active_connections",
            "request_count",
            "error_count",
        ]
        read_only_fields = ["id", "timestamp"]


class ApplicationMetricsSerializer(serializers.ModelSerializer):
    """应用指标序列化器"""

    class Meta:
        model = ApplicationMetrics
        fields = [
            "id",
            "timestamp",
            "active_users",
            "total_users",
            "new_users_today",
            "total_documents",
            "documents_uploaded_today",
            "total_document_size",
            "search_requests_today",
            "avg_search_response_time",
            "search_success_rate",
            "workflow_executions_today",
            "workflow_success_rate",
            "avg_workflow_duration",
            "error_rate",
            "critical_errors",
        ]
        read_only_fields = ["id", "timestamp"]


class MetricsQuerySerializer(serializers.Serializer):
    """指标查询序列化器"""

    metric_name = serializers.CharField(required=True, help_text="指标名称")
    start_time = serializers.DateTimeField(required=False, help_text="开始时间")
    end_time = serializers.DateTimeField(required=False, help_text="结束时间")
    interval = serializers.CharField(required=False, default="1h", help_text="时间间隔")
    labels = serializers.DictField(required=False, help_text="标签过滤")
    aggregation = serializers.ChoiceField(
        choices=["avg", "sum", "min", "max", "count"],
        required=False,
        default="avg",
        help_text="聚合方式",
    )

    def validate(self, data):
        """验证查询参数"""
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("开始时间必须早于结束时间")

        return data


class AlertRuleTestSerializer(serializers.Serializer):
    """告警规则测试序列化器"""

    metric_definition = serializers.UUIDField(required=True)
    operator = serializers.ChoiceField(
        choices=AlertRule.OPERATOR_CHOICES, required=True
    )
    threshold = serializers.FloatField(required=True)
    duration = serializers.IntegerField(required=True, min_value=0)
    test_value = serializers.FloatField(required=True, help_text="测试值")

    def validate(self, data):
        """验证测试参数"""
        try:
            MetricDefinition.objects.get(id=data["metric_definition"])
        except MetricDefinition.DoesNotExist:
            raise serializers.ValidationError("指标定义不存在")

        return data


class DashboardExportSerializer(serializers.Serializer):
    """仪表板导出序列化器"""

    format = serializers.ChoiceField(
        choices=["json", "yaml"], default="json", help_text="导出格式"
    )
    include_data = serializers.BooleanField(default=False, help_text="是否包含数据")


class MetricsExportSerializer(serializers.Serializer):
    """指标导出序列化器"""

    metric_definitions = serializers.ListField(
        child=serializers.UUIDField(), required=True, help_text="指标定义ID列表"
    )
    start_time = serializers.DateTimeField(required=True, help_text="开始时间")
    end_time = serializers.DateTimeField(required=True, help_text="结束时间")
    format = serializers.ChoiceField(
        choices=["csv", "json", "prometheus"], default="csv", help_text="导出格式"
    )

    def validate(self, data):
        """验证导出参数"""
        start_time = data["start_time"]
        end_time = data["end_time"]

        if start_time >= end_time:
            raise serializers.ValidationError("开始时间必须早于结束时间")

        # 验证指标定义存在
        metric_ids = data["metric_definitions"]
        existing_count = MetricDefinition.objects.filter(id__in=metric_ids).count()
        if existing_count != len(metric_ids):
            raise serializers.ValidationError("部分指标定义不存在")

        return data
