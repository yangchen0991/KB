"""
监控系统状态查看管理命令
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.monitoring.alert_engine import alert_engine
from apps.monitoring.models import (
    AlertInstance,
    AlertRule,
    ApplicationMetrics,
    MetricData,
    MetricDefinition,
    SystemMetrics,
)


class Command(BaseCommand):
    help = "查看监控系统状态"

    def add_arguments(self, parser):
        parser.add_argument("--detailed", action="store_true", help="显示详细信息")
        parser.add_argument("--alerts", action="store_true", help="显示告警信息")
        parser.add_argument("--metrics", action="store_true", help="显示指标信息")

    def handle(self, *args, **options):
        detailed = options["detailed"]
        show_alerts = options["alerts"]
        show_metrics = options["metrics"]

        self.stdout.write(self.style.SUCCESS("=== 监控系统状态 ==="))

        # 显示基本状态
        self.show_basic_status()

        if show_metrics or detailed:
            self.show_metrics_status()

        if show_alerts or detailed:
            self.show_alerts_status()

        if detailed:
            self.show_detailed_status()

        self.stdout.write(self.style.SUCCESS("=================="))

    def show_basic_status(self):
        """显示基本状态"""
        self.stdout.write("\n--- 基本状态 ---")

        # 指标统计
        total_metrics = MetricDefinition.objects.count()
        enabled_metrics = MetricDefinition.objects.filter(is_enabled=True).count()
        self.stdout.write(f"指标定义: {enabled_metrics}/{total_metrics} 已启用")

        # 告警统计
        total_rules = AlertRule.objects.count()
        active_rules = AlertRule.objects.filter(status="active").count()
        firing_rules = AlertRule.objects.filter(status="firing").count()
        self.stdout.write(f"告警规则: {active_rules}/{total_rules} 已激活")

        if firing_rules > 0:
            self.stdout.write(
                self.style.WARNING(f"当前告警: {firing_rules} 个规则正在告警")
            )
        else:
            self.stdout.write(self.style.SUCCESS("当前告警: 无"))

        # 数据统计
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        metrics_today = MetricData.objects.filter(timestamp__gte=today_start).count()
        alerts_today = AlertInstance.objects.filter(started_at__gte=today_start).count()

        self.stdout.write(f"今日指标数据: {metrics_today} 条")
        self.stdout.write(f"今日告警: {alerts_today} 次")

    def show_metrics_status(self):
        """显示指标状态"""
        self.stdout.write("\n--- 指标状态 ---")

        # 按类别统计
        for category, name in MetricDefinition.CATEGORY_CHOICES:
            total = MetricDefinition.objects.filter(category=category).count()
            enabled = MetricDefinition.objects.filter(
                category=category, is_enabled=True
            ).count()
            if total > 0:
                self.stdout.write(f"{name}: {enabled}/{total}")

        # 最近数据统计
        recent_time = timezone.now() - timedelta(minutes=10)
        recent_data = MetricData.objects.filter(timestamp__gte=recent_time).count()
        self.stdout.write(f"最近10分钟数据: {recent_data} 条")

        # 系统指标
        latest_system = SystemMetrics.objects.first()
        if latest_system:
            self.stdout.write(
                f'最新系统指标 ({latest_system.timestamp.strftime("%H:%M:%S")}):'
            )
            self.stdout.write(f"  CPU: {latest_system.cpu_usage_percent:.1f}%")
            self.stdout.write(f"  内存: {latest_system.memory_usage_percent:.1f}%")
            self.stdout.write(f"  磁盘: {latest_system.disk_usage_percent:.1f}%")

        # 应用指标
        latest_app = ApplicationMetrics.objects.first()
        if latest_app:
            self.stdout.write(
                f'最新应用指标 ({latest_app.timestamp.strftime("%H:%M:%S")}):'
            )
            self.stdout.write(f"  活跃用户: {latest_app.active_users}")
            self.stdout.write(f"  总文档: {latest_app.total_documents}")
            self.stdout.write(f"  今日搜索: {latest_app.search_requests_today}")

    def show_alerts_status(self):
        """显示告警状态"""
        self.stdout.write("\n--- 告警状态 ---")

        # 按严重程度统计
        for severity, name in AlertRule.SEVERITY_CHOICES:
            firing_count = AlertInstance.objects.filter(
                alert_rule__severity=severity, status="firing"
            ).count()
            if firing_count > 0:
                color = (
                    self.style.ERROR
                    if severity in ["critical", "fatal"]
                    else self.style.WARNING
                )
                self.stdout.write(color(f"{name}: {firing_count} 个告警"))

        # 最近告警
        recent_alerts = AlertInstance.objects.filter(
            started_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by("-started_at")[:5]

        if recent_alerts:
            self.stdout.write("最近告警:")
            for alert in recent_alerts:
                status_color = (
                    self.style.ERROR if alert.status == "firing" else self.style.SUCCESS
                )
                self.stdout.write(
                    f'  {alert.started_at.strftime("%H:%M:%S")} '
                    f"{alert.alert_rule.name} "
                    f"({status_color(alert.status)})"
                )

    def show_detailed_status(self):
        """显示详细状态"""
        self.stdout.write("\n--- 详细状态 ---")

        # 告警引擎状态
        engine_status = "运行中" if alert_engine.running else "已停止"
        self.stdout.write(f"告警引擎: {engine_status}")
        if alert_engine.running:
            self.stdout.write(f"检查间隔: {alert_engine.check_interval}秒")

        # 数据库统计
        self.stdout.write("数据库统计:")

        # 指标数据统计
        total_metric_data = MetricData.objects.count()
        self.stdout.write(f"  指标数据总数: {total_metric_data}")

        # 按时间段统计
        now = timezone.now()
        for hours, label in [(1, "1小时"), (24, "24小时"), (168, "7天")]:
            since = now - timedelta(hours=hours)
            count = MetricData.objects.filter(timestamp__gte=since).count()
            self.stdout.write(f"  最近{label}: {count} 条")

        # 告警实例统计
        total_alert_instances = AlertInstance.objects.count()
        resolved_alerts = AlertInstance.objects.filter(status="resolved").count()
        self.stdout.write(f"  告警实例总数: {total_alert_instances}")
        self.stdout.write(f"  已解决告警: {resolved_alerts}")

        # 存储使用情况
        self.show_storage_usage()

    def show_storage_usage(self):
        """显示存储使用情况"""
        self.stdout.write("存储使用情况:")

        # 计算各表的大小（估算）
        tables = [
            ("指标数据", MetricData.objects.count()),
            ("系统指标", SystemMetrics.objects.count()),
            ("应用指标", ApplicationMetrics.objects.count()),
            ("告警实例", AlertInstance.objects.count()),
        ]

        for name, count in tables:
            # 估算每条记录约1KB
            size_mb = count / 1024
            if size_mb > 1:
                self.stdout.write(f"  {name}: {count} 条 (~{size_mb:.1f}MB)")
            else:
                self.stdout.write(f"  {name}: {count} 条")

        # 数据保留建议
        old_data_count = MetricData.objects.filter(
            timestamp__lt=timezone.now() - timedelta(days=30)
        ).count()

        if old_data_count > 0:
            self.stdout.write(
                self.style.WARNING(f"建议清理: {old_data_count} 条超过30天的数据")
            )
