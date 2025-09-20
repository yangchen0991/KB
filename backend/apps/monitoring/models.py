import uuid
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()


class MetricDefinition(models.Model):
    """指标定义"""

    METRIC_TYPE_CHOICES = [
        ("counter", "计数器"),
        ("gauge", "仪表盘"),
        ("histogram", "直方图"),
        ("summary", "摘要"),
    ]

    CATEGORY_CHOICES = [
        ("system", "系统指标"),
        ("application", "应用指标"),
        ("business", "业务指标"),
        ("custom", "自定义指标"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True, verbose_name="指标名称")
    description = models.TextField(verbose_name="指标描述")
    metric_type = models.CharField(
        max_length=20, choices=METRIC_TYPE_CHOICES, verbose_name="指标类型"
    )
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, verbose_name="指标分类"
    )

    # Prometheus配置
    prometheus_name = models.CharField(max_length=200, verbose_name="Prometheus指标名")
    labels = models.JSONField(default=list, verbose_name="标签定义")
    help_text = models.TextField(blank=True, verbose_name="帮助文本")

    # 采集配置
    collection_interval = models.IntegerField(default=60, verbose_name="采集间隔(秒)")
    is_enabled = models.BooleanField(default=True, verbose_name="是否启用")

    # 存储配置
    retention_days = models.IntegerField(default=30, verbose_name="保留天数")

    # 元数据
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="创建者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        app_label = 'monitoring'
        db_table = "monitoring_metric_definition"
        verbose_name = "指标定义"
        verbose_name_plural = "指标定义"
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_metric_type_display()})"


class MetricData(models.Model):
    """指标数据"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_definition = models.ForeignKey(
        MetricDefinition,
        on_delete=models.CASCADE,
        related_name="data_points",
        verbose_name="指标定义",
    )

    # 时间戳
    timestamp = models.DateTimeField(verbose_name="时间戳", db_index=True)

    # 指标值
    value = models.FloatField(verbose_name="指标值")

    # 标签值
    labels = models.JSONField(default=dict, verbose_name="标签值")

    # 元数据
    instance = models.CharField(max_length=200, blank=True, verbose_name="实例标识")
    job = models.CharField(max_length=100, blank=True, verbose_name="任务名称")

    class Meta:
        app_label = 'monitoring'
        db_table = "monitoring_metric_data"
        verbose_name = "指标数据"
        verbose_name_plural = "指标数据"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["metric_definition", "timestamp"]),
            models.Index(fields=["timestamp"]),
            models.Index(fields=["instance", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.metric_definition.name}: {self.value} @ {self.timestamp}"


class AlertRule(models.Model):
    """告警规则"""

    SEVERITY_CHOICES = [
        ("info", "信息"),
        ("warning", "警告"),
        ("critical", "严重"),
        ("fatal", "致命"),
    ]

    OPERATOR_CHOICES = [
        (">", "大于"),
        (">=", "大于等于"),
        ("<", "小于"),
        ("<=", "小于等于"),
        ("==", "等于"),
        ("!=", "不等于"),
    ]

    STATUS_CHOICES = [
        ("active", "激活"),
        ("inactive", "未激活"),
        ("firing", "告警中"),
        ("resolved", "已解决"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="规则名称")
    description = models.TextField(verbose_name="规则描述")

    # 规则配置
    metric_definition = models.ForeignKey(
        MetricDefinition,
        on_delete=models.CASCADE,
        related_name="alert_rules",
        verbose_name="监控指标",
    )
    operator = models.CharField(
        max_length=5, choices=OPERATOR_CHOICES, verbose_name="比较操作符"
    )
    threshold = models.FloatField(verbose_name="阈值")
    duration = models.IntegerField(default=300, verbose_name="持续时间(秒)")

    # 告警配置
    severity = models.CharField(
        max_length=20, choices=SEVERITY_CHOICES, verbose_name="严重程度"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="active", verbose_name="状态"
    )

    # 通知配置
    notification_channels = models.JSONField(default=list, verbose_name="通知渠道")
    notification_template = models.TextField(blank=True, verbose_name="通知模板")

    # 抑制配置
    silence_duration = models.IntegerField(default=3600, verbose_name="静默时间(秒)")
    max_alerts_per_hour = models.IntegerField(
        default=10, verbose_name="每小时最大告警数"
    )

    # 元数据
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="创建者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    # 统计信息
    total_alerts = models.IntegerField(default=0, verbose_name="总告警次数")
    last_alert_at = models.DateTimeField(
        null=True, blank=True, verbose_name="最后告警时间"
    )

    class Meta:
        app_label = 'monitoring'
        db_table = "monitoring_alert_rule"
        verbose_name = "告警规则"
        verbose_name_plural = "告警规则"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_severity_display()})"

    def is_firing(self):
        """检查是否正在告警"""
        return self.status == "firing"

    def can_send_alert(self):
        """检查是否可以发送告警"""
        if not self.is_active():
            return False

        # 检查频率限制
        if self.last_alert_at:
            time_since_last = datetime.now() - self.last_alert_at
            if time_since_last.total_seconds() < self.silence_duration:
                return False

        return True

    def is_active(self):
        """检查规则是否激活"""
        return self.status == "active"


class AlertInstance(models.Model):
    """告警实例"""

    STATUS_CHOICES = [
        ("firing", "告警中"),
        ("resolved", "已解决"),
        ("silenced", "已静默"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_rule = models.ForeignKey(
        AlertRule,
        on_delete=models.CASCADE,
        related_name="instances",
        verbose_name="告警规则",
    )

    # 告警信息
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, verbose_name="状态"
    )
    message = models.TextField(verbose_name="告警消息")

    # 时间信息
    started_at = models.DateTimeField(verbose_name="开始时间")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="解决时间")

    # 触发数据
    trigger_value = models.FloatField(verbose_name="触发值")
    trigger_labels = models.JSONField(default=dict, verbose_name="触发标签")

    # 通知状态
    notifications_sent = models.JSONField(default=list, verbose_name="已发送通知")
    notification_count = models.IntegerField(default=0, verbose_name="通知次数")

    class Meta:
        app_label = 'monitoring'
        db_table = "monitoring_alert_instance"
        verbose_name = "告警实例"
        verbose_name_plural = "告警实例"
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.alert_rule.name} - {self.status} @ {self.started_at}"

    @property
    def duration(self):
        """告警持续时间"""
        end_time = self.resolved_at or datetime.now()
        return end_time - self.started_at

    def resolve(self):
        """解决告警"""
        self.status = "resolved"
        self.resolved_at = datetime.now()
        self.save()


class Dashboard(models.Model):
    """监控仪表板"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="仪表板名称")
    description = models.TextField(blank=True, verbose_name="描述")

    # 仪表板配置
    layout = models.JSONField(default=dict, verbose_name="布局配置")
    panels = models.JSONField(default=list, verbose_name="面板配置")

    # 访问控制
    is_public = models.BooleanField(default=False, verbose_name="是否公开")
    allowed_users = models.ManyToManyField(
        User, blank=True, related_name="dashboards", verbose_name="允许访问的用户"
    )

    # 元数据
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_dashboards",
        verbose_name="创建者",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    # 统计信息
    view_count = models.IntegerField(default=0, verbose_name="查看次数")
    last_viewed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="最后查看时间"
    )

    class Meta:
        app_label = 'monitoring'
        db_table = "monitoring_dashboard"
        verbose_name = "监控仪表板"
        verbose_name_plural = "监控仪表板"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class SystemMetrics(models.Model):
    """系统指标快照"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(
        auto_now_add=True, verbose_name="时间戳", db_index=True
    )

    # CPU指标
    cpu_usage_percent = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="CPU使用率(%)",
    )
    cpu_load_1m = models.FloatField(verbose_name="1分钟负载")
    cpu_load_5m = models.FloatField(verbose_name="5分钟负载")
    cpu_load_15m = models.FloatField(verbose_name="15分钟负载")

    # 内存指标
    memory_usage_percent = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="内存使用率(%)",
    )
    memory_used_bytes = models.BigIntegerField(verbose_name="已使用内存(字节)")
    memory_total_bytes = models.BigIntegerField(verbose_name="总内存(字节)")

    # 磁盘指标
    disk_usage_percent = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="磁盘使用率(%)",
    )
    disk_used_bytes = models.BigIntegerField(verbose_name="已使用磁盘(字节)")
    disk_total_bytes = models.BigIntegerField(verbose_name="总磁盘(字节)")

    # 网络指标
    network_bytes_sent = models.BigIntegerField(
        default=0, verbose_name="网络发送字节数"
    )
    network_bytes_recv = models.BigIntegerField(
        default=0, verbose_name="网络接收字节数"
    )

    # 应用指标
    active_connections = models.IntegerField(default=0, verbose_name="活跃连接数")
    request_count = models.IntegerField(default=0, verbose_name="请求总数")
    error_count = models.IntegerField(default=0, verbose_name="错误总数")

    class Meta:
        app_label = 'monitoring'
        db_table = "monitoring_system_metrics"
        verbose_name = "系统指标"
        verbose_name_plural = "系统指标"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"系统指标 @ {self.timestamp}"


class ApplicationMetrics(models.Model):
    """应用指标快照"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(
        auto_now_add=True, verbose_name="时间戳", db_index=True
    )

    # 用户指标
    active_users = models.IntegerField(default=0, verbose_name="活跃用户数")
    total_users = models.IntegerField(default=0, verbose_name="总用户数")
    new_users_today = models.IntegerField(default=0, verbose_name="今日新用户")

    # 文档指标
    total_documents = models.IntegerField(default=0, verbose_name="文档总数")
    documents_uploaded_today = models.IntegerField(
        default=0, verbose_name="今日上传文档"
    )
    total_document_size = models.BigIntegerField(
        default=0, verbose_name="文档总大小(字节)"
    )

    # 搜索指标
    search_requests_today = models.IntegerField(default=0, verbose_name="今日搜索请求")
    avg_search_response_time = models.FloatField(
        default=0, verbose_name="平均搜索响应时间(ms)"
    )
    search_success_rate = models.FloatField(default=0, verbose_name="搜索成功率(%)")

    # 工作流指标
    workflow_executions_today = models.IntegerField(
        default=0, verbose_name="今日工作流执行"
    )
    workflow_success_rate = models.FloatField(default=0, verbose_name="工作流成功率(%)")
    avg_workflow_duration = models.FloatField(
        default=0, verbose_name="平均工作流执行时间(秒)"
    )

    # 错误指标
    error_rate = models.FloatField(default=0, verbose_name="错误率(%)")
    critical_errors = models.IntegerField(default=0, verbose_name="严重错误数")

    class Meta:
        app_label = 'monitoring'
        db_table = "monitoring_application_metrics"
        verbose_name = "应用指标"
        verbose_name_plural = "应用指标"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"应用指标 @ {self.timestamp}"
