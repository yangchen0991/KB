from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    NodeExecution,
    WorkflowExecution,
    WorkflowSchedule,
    WorkflowTemplate,
    WorkflowVariable,
)

User = get_user_model()


class WorkflowTemplateSerializer(serializers.ModelSerializer):
    """工作流模板序列化器"""

    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )
    success_rate = serializers.ReadOnlyField()

    class Meta:
        model = WorkflowTemplate
        fields = [
            "id",
            "name",
            "description",
            "version",
            "status",
            "definition",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
            "execution_count",
            "success_count",
            "success_rate",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "created_at",
            "updated_at",
            "execution_count",
            "success_count",
        ]

    def validate_definition(self, value):
        """验证工作流定义"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("工作流定义必须是有效的JSON对象")

        required_fields = ["nodes", "edges"]
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"工作流定义缺少必需字段: {field}")

        return value


class WorkflowExecutionSerializer(serializers.ModelSerializer):
    """工作流执行序列化器"""

    template_name = serializers.CharField(source="template.name", read_only=True)
    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )
    duration = serializers.ReadOnlyField()
    is_finished = serializers.ReadOnlyField()

    class Meta:
        model = WorkflowExecution
        fields = [
            "id",
            "template",
            "template_name",
            "status",
            "priority",
            "input_data",
            "output_data",
            "context",
            "created_by",
            "created_by_name",
            "created_at",
            "started_at",
            "completed_at",
            "error_message",
            "retry_count",
            "max_retries",
            "duration",
            "is_finished",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "created_at",
            "started_at",
            "completed_at",
            "output_data",
            "context",
            "error_message",
        ]


class NodeExecutionSerializer(serializers.ModelSerializer):
    """节点执行序列化器"""

    duration = serializers.ReadOnlyField()

    class Meta:
        model = NodeExecution
        fields = [
            "id",
            "workflow_execution",
            "node_id",
            "node_type",
            "node_name",
            "status",
            "input_data",
            "output_data",
            "started_at",
            "completed_at",
            "error_message",
            "retry_count",
            "duration",
        ]
        read_only_fields = [
            "id",
            "started_at",
            "completed_at",
            "output_data",
            "error_message",
            "retry_count",
        ]


class WorkflowScheduleSerializer(serializers.ModelSerializer):
    """工作流调度序列化器"""

    template_name = serializers.CharField(source="template.name", read_only=True)
    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )

    class Meta:
        model = WorkflowSchedule
        fields = [
            "id",
            "template",
            "template_name",
            "name",
            "schedule_type",
            "schedule_config",
            "status",
            "input_data",
            "priority",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
            "last_run_at",
            "next_run_at",
            "execution_count",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "created_at",
            "updated_at",
            "last_run_at",
            "next_run_at",
            "execution_count",
        ]


class WorkflowVariableSerializer(serializers.ModelSerializer):
    """工作流变量序列化器"""

    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )

    class Meta:
        model = WorkflowVariable
        fields = [
            "id",
            "name",
            "description",
            "scope",
            "data_type",
            "value",
            "default_value",
            "template",
            "execution",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
            "is_encrypted",
            "is_required",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class WorkflowExecutionCreateSerializer(serializers.Serializer):
    """工作流执行创建序列化器"""

    template_id = serializers.UUIDField()
    input_data = serializers.JSONField(default=dict)
    priority = serializers.ChoiceField(
        choices=WorkflowExecution.PRIORITY_CHOICES, default="normal"
    )

    def validate_template_id(self, value):
        """验证模板ID"""
        try:
            template = WorkflowTemplate.objects.get(id=value)
            if template.status != "active":
                raise serializers.ValidationError("只能执行激活状态的工作流模板")
            return value
        except WorkflowTemplate.DoesNotExist:
            raise serializers.ValidationError("工作流模板不存在")


class NodeSchemaSerializer(serializers.Serializer):
    """节点模式序列化器"""

    type = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    inputs = serializers.JSONField()
    outputs = serializers.JSONField()
    config_schema = serializers.JSONField()


class WorkflowExecutionStatusSerializer(serializers.Serializer):
    """工作流执行状态序列化器"""

    id = serializers.UUIDField()
    status = serializers.CharField()
    started_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField(allow_null=True)
    duration = serializers.DurationField(allow_null=True)
    progress = serializers.FloatField()
    nodes = NodeExecutionSerializer(many=True)
