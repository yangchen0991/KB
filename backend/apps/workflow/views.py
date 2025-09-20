import logging

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .engine import workflow_engine
from .models import (
    NodeExecution,
    WorkflowExecution,
    WorkflowSchedule,
    WorkflowTemplate,
    WorkflowVariable,
)
from .nodes.registry import node_registry
from .serializers import (
    NodeExecutionSerializer,
    NodeSchemaSerializer,
    WorkflowExecutionCreateSerializer,
    WorkflowExecutionSerializer,
    WorkflowExecutionStatusSerializer,
    WorkflowScheduleSerializer,
    WorkflowTemplateSerializer,
    WorkflowVariableSerializer,
)

logger = logging.getLogger(__name__)


class WorkflowTemplateViewSet(viewsets.ModelViewSet):
    """工作流模板视图集"""

    queryset = WorkflowTemplate.objects.all()
    serializer_class = WorkflowTemplateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()

        # 过滤参数
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def execute(self, request, pk=None):
        """执行工作流"""
        template = self.get_object()

        serializer = WorkflowExecutionCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                execution = workflow_engine.execute_workflow(
                    template=template,
                    input_data=serializer.validated_data.get("input_data", {}),
                    user=request.user,
                    priority=serializer.validated_data.get("priority", "normal"),
                )

                execution_serializer = WorkflowExecutionSerializer(execution)
                return Response(
                    execution_serializer.data, status=status.HTTP_201_CREATED
                )

            except Exception as e:
                logger.error(f"工作流执行失败: {str(e)}")
                return Response(
                    {"error": f"工作流执行失败: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        """复制工作流模板"""
        template = self.get_object()

        # 创建副本
        new_template = WorkflowTemplate.objects.create(
            name=f"{template.name} (副本)",
            description=template.description,
            definition=template.definition,
            created_by=request.user,
        )

        serializer = WorkflowTemplateSerializer(new_template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """激活工作流模板"""
        template = self.get_object()
        template.status = "active"
        template.save()

        return Response({"message": "工作流模板已激活"})

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        """归档工作流模板"""
        template = self.get_object()
        template.status = "archived"
        template.save()

        return Response({"message": "工作流模板已归档"})


class WorkflowExecutionViewSet(viewsets.ModelViewSet):
    """工作流执行视图集"""

    queryset = WorkflowExecution.objects.all()
    serializer_class = WorkflowExecutionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # 过滤参数
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        template_id = self.request.query_params.get("template_id")
        if template_id:
            queryset = queryset.filter(template_id=template_id)

        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        """暂停工作流执行"""
        execution = self.get_object()

        if workflow_engine.pause_execution(str(execution.id)):
            return Response({"message": "工作流执行已暂停"})
        else:
            return Response(
                {"error": "无法暂停工作流执行"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        """恢复工作流执行"""
        execution = self.get_object()

        if workflow_engine.resume_execution(str(execution.id)):
            return Response({"message": "工作流执行已恢复"})
        else:
            return Response(
                {"error": "无法恢复工作流执行"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """取消工作流执行"""
        execution = self.get_object()

        if workflow_engine.cancel_execution(str(execution.id)):
            return Response({"message": "工作流执行已取消"})
        else:
            return Response(
                {"error": "无法取消工作流执行"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        """重试工作流执行"""
        execution = self.get_object()

        if not execution.can_retry():
            return Response(
                {"error": "工作流执行无法重试"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 创建新的执行实例
            new_execution = workflow_engine.execute_workflow(
                template=execution.template,
                input_data=execution.input_data,
                user=request.user,
                priority=execution.priority,
            )

            # 更新原执行的重试次数
            execution.retry_count += 1
            execution.save()

            serializer = WorkflowExecutionSerializer(new_execution)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": f"工作流重试失败: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["get"])
    def status(self, request, pk=None):
        """获取工作流执行状态"""
        execution = self.get_object()

        status_data = workflow_engine.get_execution_status(str(execution.id))
        if status_data:
            return Response(status_data)
        else:
            return Response(
                {"error": "无法获取执行状态"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=["get"])
    def logs(self, request, pk=None):
        """获取工作流执行日志"""
        execution = self.get_object()

        # 获取节点执行记录
        node_executions = execution.node_executions.all().order_by("started_at")

        logs = []
        for node_exec in node_executions:
            logs.append(
                {
                    "timestamp": node_exec.started_at,
                    "level": "INFO",
                    "message": f"开始执行节点: {node_exec.node_name}",
                    "node_id": node_exec.node_id,
                }
            )

            if node_exec.completed_at:
                level = "ERROR" if node_exec.status == "failed" else "INFO"
                message = f"节点执行{'失败' if node_exec.status == 'failed' else '完成'}: {node_exec.node_name}"
                if node_exec.error_message:
                    message += f" - {node_exec.error_message}"

                logs.append(
                    {
                        "timestamp": node_exec.completed_at,
                        "level": level,
                        "message": message,
                        "node_id": node_exec.node_id,
                    }
                )

        return Response({"logs": logs})


class NodeExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """节点执行视图集"""

    queryset = NodeExecution.objects.all()
    serializer_class = NodeExecutionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        workflow_execution_id = self.request.query_params.get("workflow_execution_id")
        if workflow_execution_id:
            queryset = queryset.filter(workflow_execution_id=workflow_execution_id)

        return queryset.order_by("started_at")


class WorkflowScheduleViewSet(viewsets.ModelViewSet):
    """工作流调度视图集"""

    queryset = WorkflowSchedule.objects.all()
    serializer_class = WorkflowScheduleSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def enable(self, request, pk=None):
        """启用调度"""
        schedule = self.get_object()
        schedule.status = "active"
        schedule.save()

        return Response({"message": "调度已启用"})

    @action(detail=True, methods=["post"])
    def disable(self, request, pk=None):
        """禁用调度"""
        schedule = self.get_object()
        schedule.status = "disabled"
        schedule.save()

        return Response({"message": "调度已禁用"})


class WorkflowVariableViewSet(viewsets.ModelViewSet):
    """工作流变量视图集"""

    queryset = WorkflowVariable.objects.all()
    serializer_class = WorkflowVariableSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()

        scope = self.request.query_params.get("scope")
        if scope:
            queryset = queryset.filter(scope=scope)

        template_id = self.request.query_params.get("template_id")
        if template_id:
            queryset = queryset.filter(template_id=template_id)

        execution_id = self.request.query_params.get("execution_id")
        if execution_id:
            queryset = queryset.filter(execution_id=execution_id)

        return queryset.order_by("name")


class WorkflowNodeViewSet(viewsets.ViewSet):
    """工作流节点视图集"""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def types(self, request):
        """获取所有节点类型"""
        schemas = node_registry.get_all_schemas()
        return Response(schemas)

    @action(detail=True, methods=["get"])
    def schema(self, request, pk=None):
        """获取节点模式"""
        schema = node_registry.get_node_schema(pk)
        if schema:
            return Response(schema)
        else:
            return Response(
                {"error": "节点类型不存在"}, status=status.HTTP_404_NOT_FOUND
            )
