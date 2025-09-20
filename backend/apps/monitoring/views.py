"""
监控系统视图
"""

import logging
from datetime import datetime, timedelta

from django.core.cache import cache
from django.db.models import Avg, Count, Max, Min, Q, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from .alert_engine import alert_engine
from .models import (
    AlertInstance,
    AlertRule,
    ApplicationMetrics,
    Dashboard,
    MetricData,
    MetricDefinition,
    SystemMetrics,
)
from .prometheus_client import prometheus_client
from .serializers import (
    AlertInstanceSerializer,
    AlertRuleSerializer,
    AlertRuleTestSerializer,
    ApplicationMetricsSerializer,
    DashboardExportSerializer,
    DashboardSerializer,
    MetricDataSerializer,
    MetricDefinitionSerializer,
    MetricsExportSerializer,
    MetricsQuerySerializer,
    SystemMetricsSerializer,
)

logger = logging.getLogger(__name__)


class MetricDefinitionViewSet(viewsets.ModelViewSet):
    """指标定义视图集"""

    queryset = MetricDefinition.objects.all()
    serializer_class = MetricDefinitionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """创建指标定义"""
        serializer.save(created_by=self.request.user)

        # 在Prometheus中创建指标
        definition = serializer.instance
        prometheus_client.create_metric(definition)

    def perform_update(self, serializer):
        """更新指标定义"""
        serializer.save()

        # 更新Prometheus指标
        definition = serializer.instance
        prometheus_client.create_metric(definition)

    @action(detail=True, methods=["post"])
    def enable(self, request, pk=None):
        """启用指标"""
        definition = self.get_object()
        definition.is_enabled = True
        definition.save()

        # 在Prometheus中创建指标
        prometheus_client.create_metric(definition)

        return Response({"status": "enabled"})

    @action(detail=True, methods=["post"])
    def disable(self, request, pk=None):
        """禁用指标"""
        definition = self.get_object()
        definition.is_enabled = False
        definition.save()

        return Response({"status": "disabled"})

    @action(detail=True, methods=["get"])
    def data(self, request, pk=None):
        """获取指标数据"""
        definition = self.get_object()

        # 获取查询参数
        start_time = request.query_params.get("start_time")
        end_time = request.query_params.get("end_time")
        limit = int(request.query_params.get("limit", 100))

        # 构建查询
        queryset = MetricData.objects.filter(metric_definition=definition)

        if start_time:
            queryset = queryset.filter(timestamp__gte=start_time)
        if end_time:
            queryset = queryset.filter(timestamp__lte=end_time)

        # 限制返回数量
        queryset = queryset.order_by("-timestamp")[:limit]

        serializer = MetricDataSerializer(queryset, many=True)
        return Response(serializer.data)


class MetricDataViewSet(viewsets.ReadOnlyModelViewSet):
    """指标数据视图集"""

    queryset = MetricData.objects.all()
    serializer_class = MetricDataSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """过滤查询集"""
        queryset = super().get_queryset()

        # 按指标定义过滤
        metric_definition = self.request.query_params.get("metric_definition")
        if metric_definition:
            queryset = queryset.filter(metric_definition=metric_definition)

        # 按时间范围过滤
        start_time = self.request.query_params.get("start_time")
        end_time = self.request.query_params.get("end_time")

        if start_time:
            queryset = queryset.filter(timestamp__gte=start_time)
        if end_time:
            queryset = queryset.filter(timestamp__lte=end_time)

        return queryset.order_by("-timestamp")


class AlertRuleViewSet(viewsets.ModelViewSet):
    """告警规则视图集"""

    queryset = AlertRule.objects.all()
    serializer_class = AlertRuleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """创建告警规则"""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """激活告警规则"""
        rule = self.get_object()
        rule.status = "active"
        rule.save()

        return Response({"status": "activated"})

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """停用告警规则"""
        rule = self.get_object()
        rule.status = "inactive"
        rule.save()

        return Response({"status": "deactivated"})

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        """测试告警规则"""
        rule = self.get_object()
        serializer = AlertRuleTestSerializer(data=request.data)

        if serializer.is_valid():
            test_value = serializer.validated_data["test_value"]

            # 模拟告警检查
            would_trigger = alert_engine.evaluate_rule(rule, test_value)

            return Response(
                {
                    "would_trigger": would_trigger,
                    "test_value": test_value,
                    "threshold": rule.threshold,
                    "operator": rule.operator,
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def instances(self, request, pk=None):
        """获取告警实例"""
        rule = self.get_object()
        instances = rule.instances.all().order_by("-started_at")

        serializer = AlertInstanceSerializer(instances, many=True)
        return Response(serializer.data)


class AlertInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    """告警实例视图集"""

    queryset = AlertInstance.objects.all()
    serializer_class = AlertInstanceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """过滤查询集"""
        queryset = super().get_queryset()

        # 按状态过滤
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # 按严重程度过滤
        severity = self.request.query_params.get("severity")
        if severity:
            queryset = queryset.filter(alert_rule__severity=severity)

        return queryset.order_by("-started_at")

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """解决告警"""
        instance = self.get_object()
        instance.resolve()

        return Response({"status": "resolved"})

    @action(detail=True, methods=["post"])
    def silence(self, request, pk=None):
        """静默告警"""
        instance = self.get_object()
        instance.status = "silenced"
        instance.save()

        return Response({"status": "silenced"})


class DashboardViewSet(viewsets.ModelViewSet):
    """仪表板视图集"""

    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """过滤查询集"""
        queryset = super().get_queryset()
        user = self.request.user

        # 只返回用户有权限访问的仪表板
        return queryset.filter(
            Q(is_public=True) | Q(created_by=user) | Q(allowed_users=user)
        ).distinct()

    def perform_create(self, serializer):
        """创建仪表板"""
        serializer.save(created_by=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """获取仪表板详情"""
        response = super().retrieve(request, *args, **kwargs)

        # 更新查看统计
        dashboard = self.get_object()
        dashboard.view_count += 1
        dashboard.last_viewed_at = timezone.now()
        dashboard.save(update_fields=["view_count", "last_viewed_at"])

        return response

    @action(detail=True, methods=["post"])
    def clone(self, request, pk=None):
        """克隆仪表板"""
        dashboard = self.get_object()

        # 创建副本
        new_dashboard = Dashboard.objects.create(
            name=f"{dashboard.name} (副本)",
            description=dashboard.description,
            layout=dashboard.layout,
            panels=dashboard.panels,
            is_public=False,
            created_by=request.user,
        )

        serializer = self.get_serializer(new_dashboard)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def export(self, request, pk=None):
        """导出仪表板"""
        dashboard = self.get_object()
        serializer = DashboardExportSerializer(data=request.query_params)

        if serializer.is_valid():
            export_format = serializer.validated_data["format"]
            include_data = serializer.validated_data["include_data"]

            # 构建导出数据
            export_data = {
                "name": dashboard.name,
                "description": dashboard.description,
                "layout": dashboard.layout,
                "panels": dashboard.panels,
                "exported_at": timezone.now().isoformat(),
                "exported_by": request.user.email,
            }

            if include_data:
                # 添加相关指标数据
                export_data["metrics_data"] = self._get_dashboard_metrics_data(
                    dashboard
                )

            # 根据格式返回数据
            if export_format == "json":
                response = HttpResponse(
                    content_type="application/json",
                    headers={
                        "Content-Disposition": f'attachment; filename="{dashboard.name}.json"'
                    },
                )
                import json

                json.dump(export_data, response, indent=2, ensure_ascii=False)
                return response
            elif export_format == "yaml":
                response = HttpResponse(
                    content_type="application/yaml",
                    headers={
                        "Content-Disposition": f'attachment; filename="{dashboard.name}.yaml"'
                    },
                )
                import yaml

                yaml.dump(
                    export_data, response, default_flow_style=False, allow_unicode=True
                )
                return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _get_dashboard_metrics_data(self, dashboard):
        """获取仪表板相关的指标数据"""
        # 从面板配置中提取指标名称
        metrics_data = {}

        for panel in dashboard.panels:
            if "metric" in panel:
                metric_name = panel["metric"]
                try:
                    definition = MetricDefinition.objects.get(
                        prometheus_name=metric_name
                    )
                    recent_data = MetricData.objects.filter(
                        metric_definition=definition,
                        timestamp__gte=timezone.now() - timedelta(hours=24),
                    ).order_by("-timestamp")[:100]

                    metrics_data[metric_name] = [
                        {
                            "timestamp": data.timestamp.isoformat(),
                            "value": data.value,
                            "labels": data.labels,
                        }
                        for data in recent_data
                    ]
                except MetricDefinition.DoesNotExist:
                    continue

        return metrics_data


class SystemMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """系统指标视图集"""

    queryset = SystemMetrics.objects.all()
    serializer_class = SystemMetricsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """过滤查询集"""
        queryset = super().get_queryset()

        # 按时间范围过滤
        start_time = self.request.query_params.get("start_time")
        end_time = self.request.query_params.get("end_time")

        if start_time:
            queryset = queryset.filter(timestamp__gte=start_time)
        if end_time:
            queryset = queryset.filter(timestamp__lte=end_time)

        return queryset.order_by("-timestamp")

    @action(detail=False, methods=["get"])
    def latest(self, request):
        """获取最新系统指标"""
        latest_metric = self.get_queryset().first()
        if latest_metric:
            serializer = self.get_serializer(latest_metric)
            return Response(serializer.data)
        return Response({"message": "暂无系统指标数据"})

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """获取系统指标摘要"""
        # 获取最近24小时的数据
        since = timezone.now() - timedelta(hours=24)
        queryset = self.get_queryset().filter(timestamp__gte=since)

        if not queryset.exists():
            return Response({"message": "暂无数据"})

        # 计算统计信息
        summary = queryset.aggregate(
            avg_cpu=Avg("cpu_usage_percent"),
            max_cpu=Max("cpu_usage_percent"),
            avg_memory=Avg("memory_usage_percent"),
            max_memory=Max("memory_usage_percent"),
            avg_disk=Avg("disk_usage_percent"),
            max_disk=Max("disk_usage_percent"),
            total_requests=Sum("request_count"),
            total_errors=Sum("error_count"),
        )

        return Response(summary)


class ApplicationMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """应用指标视图集"""

    queryset = ApplicationMetrics.objects.all()
    serializer_class = ApplicationMetricsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """过滤查询集"""
        queryset = super().get_queryset()

        # 按时间范围过滤
        start_time = self.request.query_params.get("start_time")
        end_time = self.request.query_params.get("end_time")

        if start_time:
            queryset = queryset.filter(timestamp__gte=start_time)
        if end_time:
            queryset = queryset.filter(timestamp__lte=end_time)

        return queryset.order_by("-timestamp")

    @action(detail=False, methods=["get"])
    def latest(self, request):
        """获取最新应用指标"""
        latest_metric = self.get_queryset().first()
        if latest_metric:
            serializer = self.get_serializer(latest_metric)
            return Response(serializer.data)
        return Response({"message": "暂无应用指标数据"})

    @action(detail=False, methods=["get"])
    def dashboard_data(self, request):
        """获取仪表板数据"""
        # 获取最新指标
        latest = self.get_queryset().first()

        # 获取趋势数据（最近7天）
        since = timezone.now() - timedelta(days=7)
        trend_data = self.get_queryset().filter(timestamp__gte=since)

        response_data = {
            "current": self.get_serializer(latest).data if latest else None,
            "trends": {
                "users": list(
                    trend_data.values("timestamp", "active_users", "total_users")
                ),
                "documents": list(
                    trend_data.values(
                        "timestamp", "total_documents", "documents_uploaded_today"
                    )
                ),
                "searches": list(
                    trend_data.values(
                        "timestamp", "search_requests_today", "avg_search_response_time"
                    )
                ),
                "workflows": list(
                    trend_data.values(
                        "timestamp",
                        "workflow_executions_today",
                        "workflow_success_rate",
                    )
                ),
            },
        }

        return Response(response_data)


class MonitoringAPIView(viewsets.ViewSet):
    """监控API视图"""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def metrics(self, request):
        """获取Prometheus格式的指标"""
        metrics_data = prometheus_client.export_metrics()
        return HttpResponse(metrics_data, content_type="text/plain")

    @action(detail=False, methods=["post"])
    def query(self, request):
        """查询指标数据"""
        serializer = MetricsQuerySerializer(data=request.data)

        if serializer.is_valid():
            query_params = serializer.validated_data

            # 从Prometheus查询数据
            prometheus_data = prometheus_client.query_prometheus(
                query_params["metric_name"],
                time_range="range" if query_params.get("start_time") else None,
            )

            if prometheus_data:
                return Response(prometheus_data)

            # 如果Prometheus不可用，从数据库查询
            return self._query_from_database(query_params)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _query_from_database(self, query_params):
        """从数据库查询指标数据"""
        try:
            metric_name = query_params["metric_name"]
            definition = MetricDefinition.objects.get(prometheus_name=metric_name)

            queryset = MetricData.objects.filter(metric_definition=definition)

            # 应用时间过滤
            if query_params.get("start_time"):
                queryset = queryset.filter(timestamp__gte=query_params["start_time"])
            if query_params.get("end_time"):
                queryset = queryset.filter(timestamp__lte=query_params["end_time"])

            # 应用标签过滤
            if query_params.get("labels"):
                for key, value in query_params["labels"].items():
                    queryset = queryset.filter(labels__contains={key: value})

            # 聚合数据
            aggregation = query_params.get("aggregation", "avg")
            if aggregation == "avg":
                result = queryset.aggregate(value=Avg("value"))
            elif aggregation == "sum":
                result = queryset.aggregate(value=Sum("value"))
            elif aggregation == "min":
                result = queryset.aggregate(value=Min("value"))
            elif aggregation == "max":
                result = queryset.aggregate(value=Max("value"))
            elif aggregation == "count":
                result = {"value": queryset.count()}

            return Response(
                {
                    "metric": metric_name,
                    "value": result["value"],
                    "aggregation": aggregation,
                    "data_points": queryset.count(),
                }
            )

        except MetricDefinition.DoesNotExist:
            return Response(
                {"error": f"指标 {metric_name} 不存在"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"])
    def health(self, request):
        """健康检查"""
        health_data = {
            "status": "healthy",
            "timestamp": timezone.now().isoformat(),
            "services": {
                "database": self._check_database(),
                "prometheus": self._check_prometheus(),
                "cache": self._check_cache(),
            },
        }

        # 检查整体状态
        all_healthy = all(
            service["status"] == "healthy"
            for service in health_data["services"].values()
        )
        health_data["status"] = "healthy" if all_healthy else "degraded"

        return Response(health_data)

    def _check_database(self):
        """检查数据库连接"""
        try:
            MetricDefinition.objects.count()
            return {"status": "healthy", "message": "数据库连接正常"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"数据库连接失败: {str(e)}"}

    def _check_prometheus(self):
        """检查Prometheus连接"""
        try:
            result = prometheus_client.query_prometheus("up")
            if result:
                return {"status": "healthy", "message": "Prometheus连接正常"}
            else:
                return {"status": "unhealthy", "message": "Prometheus查询失败"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Prometheus连接失败: {str(e)}"}

    def _check_cache(self):
        """检查缓存连接"""
        try:
            cache.set("health_check", "ok", 60)
            result = cache.get("health_check")
            if result == "ok":
                return {"status": "healthy", "message": "缓存连接正常"}
            else:
                return {"status": "unhealthy", "message": "缓存读写失败"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"缓存连接失败: {str(e)}"}

    @action(detail=False, methods=["post"])
    def export(self, request):
        """导出指标数据"""
        serializer = MetricsExportSerializer(data=request.data)

        if serializer.is_valid():
            export_params = serializer.validated_data

            # 获取指标数据
            metric_definitions = MetricDefinition.objects.filter(
                id__in=export_params["metric_definitions"]
            )

            queryset = MetricData.objects.filter(
                metric_definition__in=metric_definitions,
                timestamp__gte=export_params["start_time"],
                timestamp__lte=export_params["end_time"],
            ).order_by("metric_definition", "timestamp")

            # 根据格式导出
            export_format = export_params["format"]

            if export_format == "csv":
                return self._export_csv(queryset)
            elif export_format == "json":
                return self._export_json(queryset)
            elif export_format == "prometheus":
                return self._export_prometheus(queryset)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _export_csv(self, queryset):
        """导出CSV格式"""
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # 写入标题行
        writer.writerow(["Metric", "Timestamp", "Value", "Labels", "Instance", "Job"])

        # 写入数据行
        for data in queryset:
            writer.writerow(
                [
                    data.metric_definition.prometheus_name,
                    data.timestamp.isoformat(),
                    data.value,
                    str(data.labels),
                    data.instance,
                    data.job,
                ]
            )

        response = HttpResponse(
            output.getvalue(),
            content_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="metrics_export.csv"'
            },
        )
        return response

    def _export_json(self, queryset):
        """导出JSON格式"""
        data = []
        for metric_data in queryset:
            data.append(
                {
                    "metric": metric_data.metric_definition.prometheus_name,
                    "timestamp": metric_data.timestamp.isoformat(),
                    "value": metric_data.value,
                    "labels": metric_data.labels,
                    "instance": metric_data.instance,
                    "job": metric_data.job,
                }
            )

        response = HttpResponse(
            content_type="application/json",
            headers={
                "Content-Disposition": 'attachment; filename="metrics_export.json"'
            },
        )
        import json

        json.dump(data, response, indent=2, ensure_ascii=False)
        return response

    def _export_prometheus(self, queryset):
        """导出Prometheus格式"""
        output = []
        current_metric = None

        for data in queryset:
            metric_name = data.metric_definition.prometheus_name

            # 添加HELP和TYPE注释
            if metric_name != current_metric:
                output.append(
                    f"# HELP {metric_name} {data.metric_definition.description}"
                )
                output.append(
                    f"# TYPE {metric_name} {data.metric_definition.metric_type}"
                )
                current_metric = metric_name

            # 构建标签字符串
            labels_str = ""
            if data.labels:
                label_pairs = [f'{k}="{v}"' for k, v in data.labels.items()]
                labels_str = "{" + ",".join(label_pairs) + "}"

            # 添加指标行
            timestamp = int(data.timestamp.timestamp() * 1000)
            output.append(f"{metric_name}{labels_str} {data.value} {timestamp}")

        response = HttpResponse(
            "\n".join(output),
            content_type="text/plain",
            headers={
                "Content-Disposition": 'attachment; filename="metrics_export.txt"'
            },
        )
        return response
