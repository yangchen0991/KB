"""
工作流管理模型
"""

import json

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class WorkflowTemplate(models.Model):
    """工作流模板"""

    name = models.CharField(_("模板名称"), max_length=100)
    description = models.TextField(_("描述"), blank=True)

    # 模板配置
    config = models.JSONField(_("配置"), default=dict)

    # 触发条件
    trigger_type = models.CharField(
        _("触发类型"),
        max_length=20,
        choices=[
            ("manual", "手动触发"),
            ("upload", "文档上传"),
            ("classification", "文档分类"),
            ("schedule", "定时触发"),
            ("webhook", "Webhook触发"),
        ],
    )
    trigger_config = models.JSONField(_("触发配置"), default=dict)

    # 状态
    is_active = models.BooleanField(_("激活"), default=True)

    # 统计
    execution_count = models.PositiveIntegerField(_("执行次数"), default=0)
    success_count = models.PositiveIntegerField(_("成功次数"), default=0)

    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_workflows"
    )
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("工作流模板")
        verbose_name_plural = _("工作流模板")
        db_table = "kb_workflow_templates"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def success_rate(self):
        """成功率"""
        if self.execution_count == 0:
            return 0.0
        return (self.success_count / self.execution_count) * 100


class WorkflowExecution(models.Model):
    """工作流执行记录"""

    STATUS_CHOICES = [
        ("pending", "等待中"),
        ("running", "运行中"),
        ("completed", "已完成"),
        ("failed", "失败"),
        ("cancelled", "已取消"),
    ]

    template = models.ForeignKey(
        WorkflowTemplate, on_delete=models.CASCADE, related_name="executions"
    )

    # 执行信息
    status = models.CharField(
        _("状态"), max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    progress = models.PositiveIntegerField(_("进度"), default=0)

    # 输入输出
    input_data = models.JSONField(_("输入数据"), default=dict)
    output_data = models.JSONField(_("输出数据"), default=dict)

    # 错误信息
    error_message = models.TextField(_("错误信息"), blank=True)
    error_details = models.JSONField(_("错误详情"), default=dict, blank=True)

    # 执行时间
    started_at = models.DateTimeField(_("开始时间"), blank=True, null=True)
    completed_at = models.DateTimeField(_("完成时间"), blank=True, null=True)

    # 触发信息
    triggered_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True
    )
    trigger_data = models.JSONField(_("触发数据"), default=dict, blank=True)

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)

    class Meta:
        verbose_name = _("工作流执行")
        verbose_name_plural = _("工作流执行")
        db_table = "kb_workflow_executions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.template.name} - {self.get_status_display()}"

    @property
    def duration(self):
        """执行时长"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class WorkflowStep(models.Model):
    """工作流步骤"""

    STEP_TYPE_CHOICES = [
        ("ocr", "OCR处理"),
        ("classification", "自动分类"),
        ("notification", "发送通知"),
        ("approval", "审批"),
        ("archive", "归档"),
        ("transform", "数据转换"),
        ("webhook", "Webhook调用"),
        ("email", "发送邮件"),
        ("custom", "自定义脚本"),
    ]

    execution = models.ForeignKey(
        WorkflowExecution, on_delete=models.CASCADE, related_name="steps"
    )

    # 步骤信息
    step_name = models.CharField(_("步骤名称"), max_length=100)
    step_type = models.CharField(
        _("步骤类型"), max_length=20, choices=STEP_TYPE_CHOICES
    )
    step_order = models.PositiveIntegerField(_("执行顺序"))

    # 配置
    config = models.JSONField(_("步骤配置"), default=dict)

    # 状态
    status = models.CharField(
        _("状态"),
        max_length=20,
        choices=WorkflowExecution.STATUS_CHOICES,
        default="pending",
    )

    # 输入输出
    input_data = models.JSONField(_("输入数据"), default=dict)
    output_data = models.JSONField(_("输出数据"), default=dict)

    # 错误信息
    error_message = models.TextField(_("错误信息"), blank=True)

    # 执行时间
    started_at = models.DateTimeField(_("开始时间"), blank=True, null=True)
    completed_at = models.DateTimeField(_("完成时间"), blank=True, null=True)

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)

    class Meta:
        verbose_name = _("工作流步骤")
        verbose_name_plural = _("工作流步骤")
        db_table = "kb_workflow_steps"
        ordering = ["step_order"]
        unique_together = ["execution", "step_order"]

    def __str__(self):
        return f"{self.execution.template.name} - {self.step_name}"


class ApprovalRequest(models.Model):
    """审批请求"""

    STATUS_CHOICES = [
        ("pending", "待审批"),
        ("approved", "已批准"),
        ("rejected", "已拒绝"),
        ("cancelled", "已取消"),
    ]

    workflow_step = models.OneToOneField(
        WorkflowStep, on_delete=models.CASCADE, related_name="approval_request"
    )

    # 审批信息
    title = models.CharField(_("审批标题"), max_length=200)
    description = models.TextField(_("审批描述"))

    # 审批人
    approvers = models.ManyToManyField(User, related_name="approval_requests")
    required_approvals = models.PositiveIntegerField(_("需要审批数"), default=1)

    # 状态
    status = models.CharField(
        _("状态"), max_length=20, choices=STATUS_CHOICES, default="pending"
    )

    # 审批结果
    approved_by = models.ManyToManyField(
        User, related_name="approved_requests", blank=True
    )
    rejected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="rejected_requests",
        blank=True,
        null=True,
    )

    # 审批意见
    approval_comments = models.JSONField(_("审批意见"), default=list, blank=True)

    # 时间信息
    due_date = models.DateTimeField(_("截止时间"), blank=True, null=True)
    approved_at = models.DateTimeField(_("审批时间"), blank=True, null=True)

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)

    class Meta:
        verbose_name = _("审批请求")
        verbose_name_plural = _("审批请求")
        db_table = "kb_approval_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def approval_count(self):
        """已审批数量"""
        return self.approved_by.count()

    @property
    def is_approved(self):
        """是否已审批通过"""
        return self.approval_count >= self.required_approvals


class WorkflowSchedule(models.Model):
    """工作流调度"""

    template = models.ForeignKey(
        WorkflowTemplate, on_delete=models.CASCADE, related_name="schedules"
    )

    # 调度配置
    name = models.CharField(_("调度名称"), max_length=100)
    cron_expression = models.CharField(_("Cron表达式"), max_length=100)
    timezone = models.CharField(_("时区"), max_length=50, default="Asia/Shanghai")

    # 状态
    is_active = models.BooleanField(_("激活"), default=True)

    # 执行统计
    last_run = models.DateTimeField(_("最后执行"), blank=True, null=True)
    next_run = models.DateTimeField(_("下次执行"), blank=True, null=True)
    run_count = models.PositiveIntegerField(_("执行次数"), default=0)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("工作流调度")
        verbose_name_plural = _("工作流调度")
        db_table = "kb_workflow_schedules"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.template.name} - {self.name}"


class WorkflowWebhook(models.Model):
    """工作流Webhook"""

    template = models.ForeignKey(
        WorkflowTemplate, on_delete=models.CASCADE, related_name="webhooks"
    )

    # Webhook配置
    name = models.CharField(_("Webhook名称"), max_length=100)
    url_path = models.CharField(_("URL路径"), max_length=200, unique=True)
    secret_key = models.CharField(_("密钥"), max_length=100)

    # 验证配置
    require_authentication = models.BooleanField(_("需要认证"), default=True)
    allowed_ips = models.JSONField(_("允许的IP"), default=list, blank=True)

    # 状态
    is_active = models.BooleanField(_("激活"), default=True)

    # 统计
    call_count = models.PositiveIntegerField(_("调用次数"), default=0)
    last_called = models.DateTimeField(_("最后调用"), blank=True, null=True)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("工作流Webhook")
        verbose_name_plural = _("工作流Webhook")
        db_table = "kb_workflow_webhooks"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.template.name} - {self.name}"


class WorkflowLog(models.Model):
    """工作流日志"""

    LOG_LEVEL_CHOICES = [
        ("debug", "Debug"),
        ("info", "Info"),
        ("warning", "Warning"),
        ("error", "Error"),
        ("critical", "Critical"),
    ]

    execution = models.ForeignKey(
        WorkflowExecution, on_delete=models.CASCADE, related_name="logs"
    )
    step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.CASCADE,
        related_name="logs",
        blank=True,
        null=True,
    )

    # 日志信息
    level = models.CharField(_("日志级别"), max_length=20, choices=LOG_LEVEL_CHOICES)
    message = models.TextField(_("日志消息"))
    details = models.JSONField(_("详细信息"), default=dict, blank=True)

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)

    class Meta:
        verbose_name = _("工作流日志")
        verbose_name_plural = _("工作流日志")
        db_table = "kb_workflow_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["execution", "level"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.execution.template.name} - {self.level}: {self.message[:50]}"
