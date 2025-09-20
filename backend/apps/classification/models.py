"""
文档分类模型
"""

import os
import pickle

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class ClassificationModel(models.Model):
    """机器学习分类模型"""

    STATUS_CHOICES = [
        ("training", "训练中"),
        ("ready", "就绪"),
        ("failed", "失败"),
        ("deprecated", "已弃用"),
    ]

    name = models.CharField(_("模型名称"), max_length=100)
    description = models.TextField(_("描述"), blank=True)
    version = models.CharField(_("版本"), max_length=20)
    algorithm = models.CharField(
        _("算法"),
        max_length=50,
        choices=[
            ("naive_bayes", "朴素贝叶斯"),
            ("svm", "支持向量机"),
            ("random_forest", "随机森林"),
            ("logistic_regression", "逻辑回归"),
            ("neural_network", "神经网络"),
        ],
    )

    # 模型文件
    model_file = models.FileField(
        _("模型文件"), upload_to="ml_models/", blank=True, null=True
    )
    vectorizer_file = models.FileField(
        _("向量化器文件"), upload_to="ml_models/", blank=True, null=True
    )

    # 训练参数
    training_params = models.JSONField(_("训练参数"), default=dict)

    # 性能指标
    accuracy = models.FloatField(_("准确率"), default=0.0)
    precision = models.FloatField(_("精确率"), default=0.0)
    recall = models.FloatField(_("召回率"), default=0.0)
    f1_score = models.FloatField(_("F1分数"), default=0.0)

    # 训练数据统计
    training_samples = models.PositiveIntegerField(_("训练样本数"), default=0)
    feature_count = models.PositiveIntegerField(_("特征数量"), default=0)

    # 状态信息
    status = models.CharField(
        _("状态"), max_length=20, choices=STATUS_CHOICES, default="training"
    )
    is_active = models.BooleanField(_("激活"), default=False)

    # 创建信息
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_models"
    )
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    # 训练完成时间
    trained_at = models.DateTimeField(_("训练完成时间"), blank=True, null=True)

    class Meta:
        verbose_name = _("分类模型")
        verbose_name_plural = _("分类模型")
        db_table = "kb_classification_models"
        ordering = ["-created_at"]
        unique_together = ["name", "version"]

    def __str__(self):
        return f"{self.name} v{self.version}"

    def load_model(self):
        """加载模型"""
        if self.model_file and os.path.exists(self.model_file.path):
            with open(self.model_file.path, "rb") as f:
                return pickle.load(f)
        return None

    def load_vectorizer(self):
        """加载向量化器"""
        if self.vectorizer_file and os.path.exists(self.vectorizer_file.path):
            with open(self.vectorizer_file.path, "rb") as f:
                return pickle.load(f)
        return None

    def save_model(self, model, vectorizer=None):
        """保存模型"""
        # 保存模型
        model_filename = f"{self.name}_v{self.version}_model.pkl"
        model_path = os.path.join(settings.ML_MODEL_PATH, model_filename)

        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        with open(model_path, "wb") as f:
            pickle.dump(model, f)

        self.model_file.name = f"ml_models/{model_filename}"

        # 保存向量化器
        if vectorizer:
            vectorizer_filename = f"{self.name}_v{self.version}_vectorizer.pkl"
            vectorizer_path = os.path.join(settings.ML_MODEL_PATH, vectorizer_filename)

            with open(vectorizer_path, "wb") as f:
                pickle.dump(vectorizer, f)

            self.vectorizer_file.name = f"ml_models/{vectorizer_filename}"

        self.save()


class TrainingDataset(models.Model):
    """训练数据集"""

    name = models.CharField(_("数据集名称"), max_length=100)
    description = models.TextField(_("描述"), blank=True)

    # 数据统计
    total_samples = models.PositiveIntegerField(_("总样本数"), default=0)
    category_distribution = models.JSONField(_("分类分布"), default=dict)

    # 数据质量
    avg_text_length = models.FloatField(_("平均文本长度"), default=0.0)
    min_samples_per_category = models.PositiveIntegerField(_("每类最少样本"), default=0)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("训练数据集")
        verbose_name_plural = _("训练数据集")
        db_table = "kb_training_datasets"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class TrainingSample(models.Model):
    """训练样本"""

    dataset = models.ForeignKey(
        TrainingDataset, on_delete=models.CASCADE, related_name="samples"
    )

    # 文本内容
    text = models.TextField(_("文本内容"))

    # 标签
    category = models.ForeignKey("documents.Category", on_delete=models.CASCADE)

    # 来源信息
    source_document = models.ForeignKey(
        "documents.Document", on_delete=models.CASCADE, blank=True, null=True
    )

    # 数据质量
    text_length = models.PositiveIntegerField(_("文本长度"), default=0)
    is_validated = models.BooleanField(_("已验证"), default=False)

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)

    class Meta:
        verbose_name = _("训练样本")
        verbose_name_plural = _("训练样本")
        db_table = "kb_training_samples"
        indexes = [
            models.Index(fields=["dataset", "category"]),
        ]

    def __str__(self):
        return f"{self.category.name}: {self.text[:50]}..."

    def save(self, *args, **kwargs):
        self.text_length = len(self.text)
        super().save(*args, **kwargs)


class ClassificationRule(models.Model):
    """分类规则"""

    RULE_TYPE_CHOICES = [
        ("keyword", "关键词匹配"),
        ("regex", "正则表达式"),
        ("file_type", "文件类型"),
        ("file_name", "文件名模式"),
    ]

    name = models.CharField(_("规则名称"), max_length=100)
    description = models.TextField(_("描述"), blank=True)

    rule_type = models.CharField(
        _("规则类型"), max_length=20, choices=RULE_TYPE_CHOICES
    )
    pattern = models.TextField(_("匹配模式"))

    target_category = models.ForeignKey("documents.Category", on_delete=models.CASCADE)

    # 规则优先级
    priority = models.PositiveIntegerField(_("优先级"), default=0)

    # 规则状态
    is_active = models.BooleanField(_("激活"), default=True)

    # 统计信息
    match_count = models.PositiveIntegerField(_("匹配次数"), default=0)
    success_rate = models.FloatField(_("成功率"), default=0.0)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("分类规则")
        verbose_name_plural = _("分类规则")
        db_table = "kb_classification_rules"
        ordering = ["-priority", "name"]

    def __str__(self):
        return self.name

    def match(self, document):
        """检查文档是否匹配规则"""
        import re

        if self.rule_type == "keyword":
            keywords = [kw.strip().lower() for kw in self.pattern.split(",")]
            text = (
                f"{document.title} {document.description} {document.ocr_text}".lower()
            )
            return any(keyword in text for keyword in keywords)

        elif self.rule_type == "regex":
            text = f"{document.title} {document.description} {document.ocr_text}"
            return bool(re.search(self.pattern, text, re.IGNORECASE))

        elif self.rule_type == "file_type":
            return document.file_type.lower() in self.pattern.lower().split(",")

        elif self.rule_type == "file_name":
            return bool(re.search(self.pattern, document.file.name, re.IGNORECASE))

        return False


class ClassificationLog(models.Model):
    """分类日志"""

    METHOD_CHOICES = [
        ("manual", "手动分类"),
        ("rule", "规则分类"),
        ("ml", "机器学习"),
        ("hybrid", "混合方法"),
    ]

    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="classification_logs",
    )

    # 分类结果
    predicted_category = models.ForeignKey(
        "documents.Category",
        on_delete=models.CASCADE,
        related_name="predicted_documents",
    )
    actual_category = models.ForeignKey(
        "documents.Category",
        on_delete=models.CASCADE,
        related_name="actual_documents",
        blank=True,
        null=True,
    )

    # 分类方法
    method = models.CharField(_("分类方法"), max_length=20, choices=METHOD_CHOICES)
    confidence = models.FloatField(_("置信度"), default=0.0)

    # 使用的模型或规则
    model = models.ForeignKey(
        ClassificationModel, on_delete=models.SET_NULL, blank=True, null=True
    )
    rule = models.ForeignKey(
        ClassificationRule, on_delete=models.SET_NULL, blank=True, null=True
    )

    # 是否正确
    is_correct = models.BooleanField(_("分类正确"), default=True)

    # 执行信息
    executed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    executed_at = models.DateTimeField(_("执行时间"), auto_now_add=True)

    # 额外信息
    metadata = models.JSONField(_("元数据"), default=dict, blank=True)

    class Meta:
        verbose_name = _("分类日志")
        verbose_name_plural = _("分类日志")
        db_table = "kb_classification_logs"
        ordering = ["-executed_at"]

    def __str__(self):
        return f"{self.document.title} -> {self.predicted_category.name}"
