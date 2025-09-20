import json
import uuid
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

User = get_user_model()


class WorkflowTemplate(models.Model):
    """工作流模板"""

    STATUS_CHOICES = [
        ("draft", "草稿"),
        ("active", "激活"),
        ("archived", "归档"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="模板名称")
    description = models.TextField(blank=True, verbose_name="描述")
    version = models.CharField(max_length=20, default="1.0.0", verbose_name="版本")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="draft", verbose_name="状态"
    )

    # 工作流定义 (JSON格式)
    definition = models.JSONField(default=dict, verbose_name="工作流定义")

    # 元数据
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_workflows",
        verbose_name="创建者",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    # 统计信息
    execution_count = models.IntegerField(default=0, verbose_name="执行次数")
    success_count = models.IntegerField(default=0, verbose_name="成功次数")

    class Meta:
        app_label = 'workflow'
        db_table = "workflow_template"
        verbose_name = "工作流模板"
        verbose_name_plural = "工作流模板"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} (v{self.version})"

    def clean(self):
        """验证工作流定义"""
        if not isinstance(self.definition, dict):
            raise ValidationError("工作流定义必须是有效的JSON对象")

        required_fields = ["nodes", "edges"]
        for field in required_fields:
            if field not in self.definition:
                raise ValidationError(f"工作流定义缺少必需字段: {field}")

    @property
    def success_rate(self):
        """成功率"""
        if self.execution_count == 0:
            return 0
        return round((self.success_count / self.execution_count) * 100, 2)


class WorkflowExecution(models.Model):
    """工作流执行实例"""

    STATUS_CHOICES = [
        ("pending", "等待中"),
        ("running", "运行中"),
        ("paused", "暂停"),
        ("completed", "已完成"),
        ("failed", "失败"),
        ("cancelled", "已取消"),
    ]

    PRIORITY_CHOICES = [
        ("low", "低"),
        ("normal", "普通"),
        ("high", "高"),
        ("urgent", "紧急"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        WorkflowTemplate,
        on_delete=models.CASCADE,
        related_name="executions",
        verbose_name="工作流模板",
    )

    # 执行状态
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="状态"
    )
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="normal", verbose_name="优先级"
    )

    # 执行上下文
    input_data = models.JSONField(default=dict, verbose_name="输入数据")
    output_data = models.JSONField(default=dict, verbose_name="输出数据")
    context = models.JSONField(default=dict, verbose_name="执行上下文")

    # 时间信息
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="workflow_executions",
        verbose_name="创建者",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")

    # 错误信息
    error_message = models.TextField(blank=True, verbose_name="错误信息")
    retry_count = models.IntegerField(default=0, verbose_name="重试次数")
    max_retries = models.IntegerField(default=3, verbose_name="最大重试次数")

    class Meta:
        app_label = 'workflow'
        db_table = "workflow_execution"
        verbose_name = "工作流执行"
        verbose_name_plural = "工作流执行"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.template.name} - {self.status} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

    @property
    def duration(self):
        """执行时长"""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.now()
        return end_time - self.started_at

    @property
    def is_finished(self):
        """是否已结束"""
        return self.status in ["completed", "failed", "cancelled"]

    def can_retry(self):
        """是否可以重试"""
        return self.status == "failed" and self.retry_count < self.max_retries


class NodeExecution(models.Model):
    """节点执行记录"""

    STATUS_CHOICES = [
        ("pending", "等待中"),
        ("running", "运行中"),
        ("completed", "已完成"),
        ("failed", "失败"),
        ("skipped", "跳过"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_execution = models.ForeignKey(
        WorkflowExecution,
        on_delete=models.CASCADE,
        related_name="node_executions",
        verbose_name="工作流执行",
    )

    # 节点信息
    node_id = models.CharField(max_length=100, verbose_name="节点ID")
    node_type = models.CharField(max_length=50, verbose_name="节点类型")
    node_name = models.CharField(max_length=200, verbose_name="节点名称")

    # 执行状态
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="状态"
    )

    # 执行数据
    input_data = models.JSONField(default=dict, verbose_name="输入数据")
    output_data = models.JSONField(default=dict, verbose_name="输出数据")

    # 时间信息
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")

    # 错误信息
    error_message = models.TextField(blank=True, verbose_name="错误信息")
    retry_count = models.IntegerField(default=0, verbose_name="重试次数")

    class Meta:
        app_label = 'workflow'
        db_table = "node_execution"
        verbose_name = "节点执行"
        verbose_name_plural = "节点执行"
        ordering = ["started_at"]
        unique_together = ["workflow_execution", "node_id"]

    def __str__(self):
        return f"{self.node_name} - {self.status}"

    @property
    def duration(self):
        """执行时长"""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.now()
        return end_time - self.started_at


class WorkflowSchedule(models.Model):
    """工作流调度"""

    SCHEDULE_TYPE_CHOICES = [
        ("once", "一次性"),
        ("interval", "间隔"),
        ("cron", "Cron表达式"),
        ("event", "事件触发"),
    ]

    STATUS_CHOICES = [
        ("active", "激活"),
        ("paused", "暂停"),
        ("disabled", "禁用"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        WorkflowTemplate,
        on_delete=models.CASCADE,
        related_name="schedules",
        verbose_name="工作流模板",
    )

    # 调度配置
    name = models.CharField(max_length=200, verbose_name="调度名称")
    schedule_type = models.CharField(
        max_length=20, choices=SCHEDULE_TYPE_CHOICES, verbose_name="调度类型"
    )
    schedule_config = models.JSONField(default=dict, verbose_name="调度配置")

    # 状态
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="active", verbose_name="状态"
    )

    # 执行配置
    input_data = models.JSONField(default=dict, verbose_name="默认输入数据")
    priority = models.CharField(
        max_length=20,
        choices=WorkflowExecution.PRIORITY_CHOICES,
        default="normal",
        verbose_name="优先级",
    )

    # 时间信息
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="workflow_schedules",
        verbose_name="创建者",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    # 执行信息
    last_run_at = models.DateTimeField(
        null=True, blank=True, verbose_name="上次执行时间"
    )
    next_run_at = models.DateTimeField(
        null=True, blank=True, verbose_name="下次执行时间"
    )
    execution_count = models.IntegerField(default=0, verbose_name="执行次数")

    class Meta:
        app_label = 'workflow'
        db_table = "workflow_schedule"
        verbose_name = "工作流调度"
        verbose_name_plural = "工作流调度"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.schedule_type}"


class WorkflowVariable(models.Model):
    """工作流变量"""

    SCOPE_CHOICES = [
        ("global", "全局"),
        ("template", "模板"),
        ("execution", "执行实例"),
    ]

    TYPE_CHOICES = [
        ("string", "字符串"),
        ("number", "数字"),
        ("boolean", "布尔值"),
        ("json", "JSON对象"),
        ("file", "文件"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 变量信息
    name = models.CharField(max_length=100, verbose_name="变量名")
    description = models.TextField(blank=True, verbose_name="描述")
    scope = models.CharField(
        max_length=20, choices=SCOPE_CHOICES, verbose_name="作用域"
    )
    data_type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default="string", verbose_name="数据类型"
    )

    # 变量值
    value = models.JSONField(verbose_name="变量值")
    default_value = models.JSONField(null=True, blank=True, verbose_name="默认值")

    # 关联对象
    template = models.ForeignKey(
        WorkflowTemplate,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="variables",
        verbose_name="工作流模板",
    )
    execution = models.ForeignKey(
        WorkflowExecution,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="variables",
        verbose_name="工作流执行",
    )

    # 元数据
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="创建者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    # 配置
    is_encrypted = models.BooleanField(default=False, verbose_name="是否加密")
    is_required = models.BooleanField(default=False, verbose_name="是否必需")

    class Meta:
        app_label = 'workflow'
        db_table = "workflow_variable"
        verbose_name = "工作流变量"
        verbose_name_plural = "工作流变量"
        ordering = ["name"]
        unique_together = [
            ["name", "scope", "template"],
            ["name", "scope", "execution"],
        ]

    def __str__(self):
        return f"{self.name} ({self.scope})"
