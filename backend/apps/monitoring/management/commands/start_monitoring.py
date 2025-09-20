"""
启动监控系统管理命令
"""

import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.monitoring.alert_engine import alert_engine
from apps.monitoring.collectors import start_monitoring_collectors

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "启动监控系统（收集器和告警引擎）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--collectors-only", action="store_true", help="只启动数据收集器"
        )
        parser.add_argument("--alerts-only", action="store_true", help="只启动告警引擎")
        parser.add_argument(
            "--check-interval", type=int, default=60, help="告警检查间隔（秒）"
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("正在启动监控系统..."))

        collectors_only = options["collectors_only"]
        alerts_only = options["alerts_only"]
        check_interval = options["check_interval"]

        try:
            if not alerts_only:
                # 启动数据收集器
                self.stdout.write("启动监控数据收集器...")
                start_monitoring_collectors()
                self.stdout.write(self.style.SUCCESS("✓ 监控数据收集器已启动"))

            if not collectors_only:
                # 启动告警引擎
                self.stdout.write("启动告警引擎...")
                alert_engine.check_interval = check_interval
                alert_engine.start()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ 告警引擎已启动（检查间隔: {check_interval}秒）"
                    )
                )

            self.stdout.write(self.style.SUCCESS("监控系统启动完成！"))

            # 显示状态信息
            self.show_status()

            # 保持运行
            self.stdout.write("监控系统正在运行中，按 Ctrl+C 停止...")
            try:
                import time

                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stdout.write("\n正在停止监控系统...")
                self.stop_monitoring()
                self.stdout.write(self.style.SUCCESS("监控系统已停止"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"启动监控系统失败: {str(e)}"))
            raise

    def show_status(self):
        """显示监控系统状态"""
        from apps.monitoring.models import AlertRule, MetricDefinition

        self.stdout.write("\n=== 监控系统状态 ===")

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

        self.stdout.write("==================\n")

    def stop_monitoring(self):
        """停止监控系统"""
        try:
            from apps.monitoring.collectors import stop_monitoring_collectors

            # 停止收集器
            stop_monitoring_collectors()

            # 停止告警引擎
            alert_engine.stop()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"停止监控系统时出错: {str(e)}"))
