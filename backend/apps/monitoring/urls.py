"""
监控系统URL配置
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AlertInstanceViewSet,
    AlertRuleViewSet,
    ApplicationMetricsViewSet,
    DashboardViewSet,
    MetricDataViewSet,
    MetricDefinitionViewSet,
    MonitoringAPIView,
    SystemMetricsViewSet,
)
from .simple_views import simple_health_check

# 创建路由器
router = DefaultRouter()
router.register(r"metric-definitions", MetricDefinitionViewSet)
router.register(r"metric-data", MetricDataViewSet)
router.register(r"alert-rules", AlertRuleViewSet)
router.register(r"alert-instances", AlertInstanceViewSet)
router.register(r"dashboards", DashboardViewSet)
router.register(r"system-metrics", SystemMetricsViewSet)
router.register(r"application-metrics", ApplicationMetricsViewSet)
router.register(r"api", MonitoringAPIView, basename="monitoring-api")

app_name = "monitoring"

urlpatterns = [
    # 简单健康检查 - 不需要认证
    path("health/", simple_health_check, name="simple-health-check"),
    # 其他路由
    path("", include(router.urls)),
]
