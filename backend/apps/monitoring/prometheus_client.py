"""
Prometheus客户端集成
提供指标收集、推送和查询功能
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings
from django.utils import timezone
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Summary,
    delete_from_gateway,
    generate_latest,
    push_to_gateway,
)
from prometheus_client.parser import text_string_to_metric_families

from .models import MetricData, MetricDefinition

logger = logging.getLogger(__name__)


class PrometheusClient:
    """Prometheus客户端"""

    def __init__(self):
        self.registry = CollectorRegistry()
        self.metrics: Dict[str, Any] = {}
        self.gateway_url = getattr(
            settings, "PROMETHEUS_GATEWAY_URL", "http://localhost:9091"
        )
        self.prometheus_url = getattr(
            settings, "PROMETHEUS_URL", "http://localhost:9090"
        )
        self.job_name = getattr(settings, "PROMETHEUS_JOB_NAME", "knowledge-base")
        self.instance_name = getattr(settings, "PROMETHEUS_INSTANCE_NAME", "django-app")

        # 初始化基础指标
        self._init_basic_metrics()

        # 启动推送线程
        self._start_push_thread()

    def _init_basic_metrics(self):
        """初始化基础指标"""
        # HTTP请求指标
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
            registry=self.registry,
        )

        self.http_request_duration = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration",
            ["method", "endpoint"],
            registry=self.registry,
        )

        # 应用指标
        self.active_users = Gauge(
            "active_users_total", "Number of active users", registry=self.registry
        )

        self.document_count = Gauge(
            "documents_total", "Total number of documents", registry=self.registry
        )

        self.search_requests = Counter(
            "search_requests_total",
            "Total search requests",
            ["status"],
            registry=self.registry,
        )

        self.search_duration = Histogram(
            "search_duration_seconds", "Search request duration", registry=self.registry
        )

        # 工作流指标
        self.workflow_executions = Counter(
            "workflow_executions_total",
            "Total workflow executions",
            ["template", "status"],
            registry=self.registry,
        )

        self.workflow_duration = Histogram(
            "workflow_duration_seconds",
            "Workflow execution duration",
            ["template"],
            registry=self.registry,
        )

        # 系统指标
        self.cpu_usage = Gauge(
            "cpu_usage_percent", "CPU usage percentage", registry=self.registry
        )

        self.memory_usage = Gauge(
            "memory_usage_percent", "Memory usage percentage", registry=self.registry
        )

        self.disk_usage = Gauge(
            "disk_usage_percent", "Disk usage percentage", registry=self.registry
        )

        # 存储指标引用
        self.metrics.update(
            {
                "http_requests_total": self.http_requests_total,
                "http_request_duration": self.http_request_duration,
                "active_users": self.active_users,
                "document_count": self.document_count,
                "search_requests": self.search_requests,
                "search_duration": self.search_duration,
                "workflow_executions": self.workflow_executions,
                "workflow_duration": self.workflow_duration,
                "cpu_usage": self.cpu_usage,
                "memory_usage": self.memory_usage,
                "disk_usage": self.disk_usage,
            }
        )

    def create_metric(self, definition: MetricDefinition):
        """根据定义创建Prometheus指标"""
        metric_name = definition.prometheus_name

        if metric_name in self.metrics:
            logger.warning(f"指标 {metric_name} 已存在")
            return self.metrics[metric_name]

        labels = [label["name"] for label in definition.labels]

        try:
            if definition.metric_type == "counter":
                metric = Counter(
                    metric_name,
                    definition.help_text or definition.description,
                    labels,
                    registry=self.registry,
                )
            elif definition.metric_type == "gauge":
                metric = Gauge(
                    metric_name,
                    definition.help_text or definition.description,
                    labels,
                    registry=self.registry,
                )
            elif definition.metric_type == "histogram":
                metric = Histogram(
                    metric_name,
                    definition.help_text or definition.description,
                    labels,
                    registry=self.registry,
                )
            elif definition.metric_type == "summary":
                metric = Summary(
                    metric_name,
                    definition.help_text or definition.description,
                    labels,
                    registry=self.registry,
                )
            else:
                raise ValueError(f"不支持的指标类型: {definition.metric_type}")

            self.metrics[metric_name] = metric
            logger.info(f"创建Prometheus指标: {metric_name}")
            return metric

        except Exception as e:
            logger.error(f"创建指标失败 {metric_name}: {str(e)}")
            return None

    def record_metric(
        self, metric_name: str, value: float, labels: Dict[str, str] = None
    ):
        """记录指标值"""
        if metric_name not in self.metrics:
            logger.warning(f"指标 {metric_name} 不存在")
            return

        metric = self.metrics[metric_name]
        labels = labels or {}

        try:
            if isinstance(metric, Counter):
                if labels:
                    metric.labels(**labels).inc(value)
                else:
                    metric.inc(value)
            elif isinstance(metric, Gauge):
                if labels:
                    metric.labels(**labels).set(value)
                else:
                    metric.set(value)
            elif isinstance(metric, (Histogram, Summary)):
                if labels:
                    metric.labels(**labels).observe(value)
                else:
                    metric.observe(value)

            logger.debug(f"记录指标 {metric_name}: {value} {labels}")

        except Exception as e:
            logger.error(f"记录指标失败 {metric_name}: {str(e)}")

    def get_metric_value(
        self, metric_name: str, labels: Dict[str, str] = None
    ) -> Optional[float]:
        """获取指标当前值"""
        if metric_name not in self.metrics:
            return None

        metric = self.metrics[metric_name]

        try:
            if isinstance(metric, Gauge):
                if labels:
                    return metric.labels(**labels)._value._value
                else:
                    return metric._value._value
            elif isinstance(metric, Counter):
                if labels:
                    return metric.labels(**labels)._value._value
                else:
                    return metric._value._value

        except Exception as e:
            logger.error(f"获取指标值失败 {metric_name}: {str(e)}")
            return None

    def export_metrics(self) -> str:
        """导出指标数据"""
        try:
            return generate_latest(self.registry).decode("utf-8")
        except Exception as e:
            logger.error(f"导出指标失败: {str(e)}")
            return ""

    def push_to_gateway(self):
        """推送指标到Pushgateway"""
        try:
            push_to_gateway(
                self.gateway_url,
                job=self.job_name,
                registry=self.registry,
                grouping_key={"instance": self.instance_name},
            )
            logger.debug("指标推送到Pushgateway成功")

        except Exception as e:
            logger.error(f"推送指标到Pushgateway失败: {str(e)}")

    def delete_from_gateway(self):
        """从Pushgateway删除指标"""
        try:
            delete_from_gateway(
                self.gateway_url,
                job=self.job_name,
                grouping_key={"instance": self.instance_name},
            )
            logger.info("从Pushgateway删除指标成功")

        except Exception as e:
            logger.error(f"从Pushgateway删除指标失败: {str(e)}")

    def query_prometheus(
        self, query: str, time_range: Optional[str] = None
    ) -> Optional[Dict]:
        """查询Prometheus数据"""
        try:
            url = f"{self.prometheus_url}/api/v1/query"
            params = {"query": query}

            if time_range:
                url = f"{self.prometheus_url}/api/v1/query_range"
                params.update(
                    {
                        "start": (datetime.now() - timedelta(hours=1)).isoformat(),
                        "end": datetime.now().isoformat(),
                        "step": "60s",
                    }
                )

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            if data["status"] == "success":
                return data["data"]
            else:
                logger.error(
                    f"Prometheus查询失败: {data.get('error', 'Unknown error')}"
                )
                return None

        except Exception as e:
            logger.error(f"查询Prometheus失败: {str(e)}")
            return None

    def _start_push_thread(self):
        """启动推送线程"""

        def push_worker():
            while True:
                try:
                    self.push_to_gateway()
                    time.sleep(60)  # 每分钟推送一次
                except Exception as e:
                    logger.error(f"推送线程错误: {str(e)}")
                    time.sleep(60)

        push_thread = threading.Thread(target=push_worker, daemon=True)
        push_thread.start()
        logger.info("Prometheus推送线程已启动")

    def record_http_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ):
        """记录HTTP请求指标"""
        self.http_requests_total.labels(
            method=method, endpoint=endpoint, status=str(status_code)
        ).inc()

        self.http_request_duration.labels(method=method, endpoint=endpoint).observe(
            duration
        )

    def record_search_request(self, duration: float, success: bool = True):
        """记录搜索请求指标"""
        status = "success" if success else "error"
        self.search_requests.labels(status=status).inc()
        self.search_duration.observe(duration)

    def record_workflow_execution(
        self, template_name: str, status: str, duration: float
    ):
        """记录工作流执行指标"""
        self.workflow_executions.labels(template=template_name, status=status).inc()

        if status == "completed":
            self.workflow_duration.labels(template=template_name).observe(duration)

    def update_system_metrics(
        self, cpu_percent: float, memory_percent: float, disk_percent: float
    ):
        """更新系统指标"""
        self.cpu_usage.set(cpu_percent)
        self.memory_usage.set(memory_percent)
        self.disk_usage.set(disk_percent)

    def update_application_metrics(self, active_users: int, document_count: int):
        """更新应用指标"""
        self.active_users.set(active_users)
        self.document_count.set(document_count)

    def save_metrics_to_db(self):
        """保存指标数据到数据库"""
        try:
            timestamp = timezone.now()

            # 获取所有启用的指标定义
            metric_definitions = MetricDefinition.objects.filter(is_enabled=True)

            for definition in metric_definitions:
                metric_name = definition.prometheus_name

                if metric_name in self.metrics:
                    value = self.get_metric_value(metric_name)

                    if value is not None:
                        # 保存到数据库
                        MetricData.objects.create(
                            metric_definition=definition,
                            timestamp=timestamp,
                            value=value,
                            labels={},
                            instance=self.instance_name,
                            job=self.job_name,
                        )

            logger.debug("指标数据保存到数据库成功")

        except Exception as e:
            logger.error(f"保存指标数据到数据库失败: {str(e)}")

    def cleanup_old_data(self):
        """清理过期数据"""
        try:
            # 获取所有指标定义的保留期配置
            metric_definitions = MetricDefinition.objects.all()

            for definition in metric_definitions:
                cutoff_date = timezone.now() - timedelta(days=definition.retention_days)

                # 删除过期数据
                deleted_count = MetricData.objects.filter(
                    metric_definition=definition, timestamp__lt=cutoff_date
                ).delete()[0]

                if deleted_count > 0:
                    logger.info(
                        f"清理指标 {definition.name} 过期数据: {deleted_count} 条"
                    )

        except Exception as e:
            logger.error(f"清理过期数据失败: {str(e)}")


# 全局Prometheus客户端实例
prometheus_client = PrometheusClient()
