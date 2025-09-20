"""
初始化监控系统管理命令
创建默认的指标定义和告警规则
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.monitoring.models import AlertRule, MetricDefinition

User = get_user_model()


class Command(BaseCommand):
    help = "初始化监控系统（创建默认指标和告警规则）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--admin-email",
            type=str,
            default="admin@example.com",
            help="管理员邮箱（用于创建告警规则）",
        )
        parser.add_argument(
            "--force", action="store_true", help="强制重新创建（删除现有数据）"
        )

    def handle(self, *args, **options):
        admin_email = options["admin_email"]
        force = options["force"]

        self.stdout.write(self.style.SUCCESS("正在初始化监控系统..."))

        try:
            # 获取或创建管理员用户
            admin_user = self.get_admin_user(admin_email)

            if force:
                self.stdout.write("清理现有数据...")
                MetricDefinition.objects.all().delete()
                AlertRule.objects.all().delete()

            # 创建默认指标定义
            self.create_default_metrics(admin_user)

            # 创建默认告警规则
            self.create_default_alert_rules(admin_user)

            self.stdout.write(self.style.SUCCESS("监控系统初始化完成！"))

            # 显示创建的资源
            self.show_summary()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"初始化监控系统失败: {str(e)}"))
            raise

    def get_admin_user(self, email):
        """获取或创建管理员用户"""
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(f"创建管理员用户: {email}")
            return User.objects.create_user(
                email=email, password="admin123", is_staff=True, is_superuser=True
            )

    def create_default_metrics(self, admin_user):
        """创建默认指标定义"""
        self.stdout.write("创建默认指标定义...")

        default_metrics = [
            # 系统指标
            {
                "name": "CPU使用率",
                "description": "系统CPU使用百分比",
                "metric_type": "gauge",
                "category": "system",
                "prometheus_name": "cpu_usage_percent",
                "help_text": "CPU usage percentage",
                "labels": [],
            },
            {
                "name": "内存使用率",
                "description": "系统内存使用百分比",
                "metric_type": "gauge",
                "category": "system",
                "prometheus_name": "memory_usage_percent",
                "help_text": "Memory usage percentage",
                "labels": [],
            },
            {
                "name": "磁盘使用率",
                "description": "系统磁盘使用百分比",
                "metric_type": "gauge",
                "category": "system",
                "prometheus_name": "disk_usage_percent",
                "help_text": "Disk usage percentage",
                "labels": [],
            },
            # 应用指标
            {
                "name": "HTTP请求总数",
                "description": "HTTP请求总数",
                "metric_type": "counter",
                "category": "application",
                "prometheus_name": "http_requests_total",
                "help_text": "Total HTTP requests",
                "labels": [
                    {"name": "method", "description": "HTTP方法"},
                    {"name": "endpoint", "description": "请求端点"},
                    {"name": "status", "description": "状态码"},
                ],
            },
            {
                "name": "HTTP请求响应时间",
                "description": "HTTP请求响应时间分布",
                "metric_type": "histogram",
                "category": "application",
                "prometheus_name": "http_request_duration_seconds",
                "help_text": "HTTP request duration",
                "labels": [
                    {"name": "method", "description": "HTTP方法"},
                    {"name": "endpoint", "description": "请求端点"},
                ],
            },
            {
                "name": "活跃用户数",
                "description": "当前活跃用户数量",
                "metric_type": "gauge",
                "category": "business",
                "prometheus_name": "active_users_total",
                "help_text": "Number of active users",
                "labels": [],
            },
            {
                "name": "文档总数",
                "description": "系统中文档总数",
                "metric_type": "gauge",
                "category": "business",
                "prometheus_name": "documents_total",
                "help_text": "Total number of documents",
                "labels": [],
            },
            {
                "name": "搜索请求总数",
                "description": "搜索请求总数",
                "metric_type": "counter",
                "category": "business",
                "prometheus_name": "search_requests_total",
                "help_text": "Total search requests",
                "labels": [{"name": "status", "description": "搜索状态"}],
            },
            {
                "name": "搜索响应时间",
                "description": "搜索请求响应时间分布",
                "metric_type": "histogram",
                "category": "business",
                "prometheus_name": "search_duration_seconds",
                "help_text": "Search request duration",
                "labels": [],
            },
            {
                "name": "工作流执行总数",
                "description": "工作流执行总数",
                "metric_type": "counter",
                "category": "business",
                "prometheus_name": "workflow_executions_total",
                "help_text": "Total workflow executions",
                "labels": [
                    {"name": "template", "description": "工作流模板"},
                    {"name": "status", "description": "执行状态"},
                ],
            },
            {
                "name": "工作流执行时间",
                "description": "工作流执行时间分布",
                "metric_type": "histogram",
                "category": "business",
                "prometheus_name": "workflow_duration_seconds",
                "help_text": "Workflow execution duration",
                "labels": [{"name": "template", "description": "工作流模板"}],
            },
        ]

        created_count = 0
        for metric_data in default_metrics:
            metric, created = MetricDefinition.objects.get_or_create(
                prometheus_name=metric_data["prometheus_name"],
                defaults={**metric_data, "created_by": admin_user},
            )
            if created:
                created_count += 1
                self.stdout.write(f"  ✓ {metric.name}")

        self.stdout.write(f"创建了 {created_count} 个指标定义")

    def create_default_alert_rules(self, admin_user):
        """创建默认告警规则"""
        self.stdout.write("创建默认告警规则...")

        # 获取指标定义
        cpu_metric = MetricDefinition.objects.get(prometheus_name="cpu_usage_percent")
        memory_metric = MetricDefinition.objects.get(
            prometheus_name="memory_usage_percent"
        )
        disk_metric = MetricDefinition.objects.get(prometheus_name="disk_usage_percent")

        default_rules = [
            {
                "name": "CPU使用率过高",
                "description": "当CPU使用率超过80%时触发告警",
                "metric_definition": cpu_metric,
                "operator": ">",
                "threshold": 80.0,
                "duration": 300,  # 5分钟
                "severity": "warning",
                "notification_channels": [
                    {"type": "email", "recipients": [admin_user.email]}
                ],
            },
            {
                "name": "CPU使用率严重过高",
                "description": "当CPU使用率超过90%时触发严重告警",
                "metric_definition": cpu_metric,
                "operator": ">",
                "threshold": 90.0,
                "duration": 180,  # 3分钟
                "severity": "critical",
                "notification_channels": [
                    {"type": "email", "recipients": [admin_user.email]}
                ],
            },
            {
                "name": "内存使用率过高",
                "description": "当内存使用率超过85%时触发告警",
                "metric_definition": memory_metric,
                "operator": ">",
                "threshold": 85.0,
                "duration": 300,  # 5分钟
                "severity": "warning",
                "notification_channels": [
                    {"type": "email", "recipients": [admin_user.email]}
                ],
            },
            {
                "name": "内存使用率严重过高",
                "description": "当内存使用率超过95%时触发严重告警",
                "metric_definition": memory_metric,
                "operator": ">",
                "threshold": 95.0,
                "duration": 120,  # 2分钟
                "severity": "critical",
                "notification_channels": [
                    {"type": "email", "recipients": [admin_user.email]}
                ],
            },
            {
                "name": "磁盘空间不足",
                "description": "当磁盘使用率超过90%时触发告警",
                "metric_definition": disk_metric,
                "operator": ">",
                "threshold": 90.0,
                "duration": 600,  # 10分钟
                "severity": "critical",
                "notification_channels": [
                    {"type": "email", "recipients": [admin_user.email]}
                ],
            },
        ]

        created_count = 0
        for rule_data in default_rules:
            rule, created = AlertRule.objects.get_or_create(
                name=rule_data["name"], defaults={**rule_data, "created_by": admin_user}
            )
            if created:
                created_count += 1
                self.stdout.write(f"  ✓ {rule.name}")

        self.stdout.write(f"创建了 {created_count} 个告警规则")

    def show_summary(self):
        """显示创建摘要"""
        self.stdout.write("\n=== 初始化摘要 ===")

        # 指标统计
        total_metrics = MetricDefinition.objects.count()
        enabled_metrics = MetricDefinition.objects.filter(is_enabled=True).count()
        self.stdout.write(f"指标定义: {total_metrics} 个（{enabled_metrics} 个已启用）")

        # 按类别统计
        for category, name in MetricDefinition.CATEGORY_CHOICES:
            count = MetricDefinition.objects.filter(category=category).count()
            if count > 0:
                self.stdout.write(f"  - {name}: {count} 个")

        # 告警规则统计
        total_rules = AlertRule.objects.count()
        active_rules = AlertRule.objects.filter(status="active").count()
        self.stdout.write(f"告警规则: {total_rules} 个（{active_rules} 个已激活）")

        # 按严重程度统计
        for severity, name in AlertRule.SEVERITY_CHOICES:
            count = AlertRule.objects.filter(severity=severity).count()
            if count > 0:
                self.stdout.write(f"  - {name}: {count} 个")

        self.stdout.write("==================\n")

        self.stdout.write(
            self.style.SUCCESS(
                "提示: 使用 python manage.py start_monitoring 启动监控系统"
            )
        )
