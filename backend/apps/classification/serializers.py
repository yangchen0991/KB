"""
文档分类序列化器
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    ClassificationLog,
    ClassificationModel,
    ClassificationRule,
    TrainingDataset,
    TrainingSample,
)

User = get_user_model()


class ClassificationModelSerializer(serializers.ModelSerializer):
    """分类模型序列化器"""

    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    algorithm_display = serializers.CharField(
        source="get_algorithm_display", read_only=True
    )

    class Meta:
        model = ClassificationModel
        fields = [
            "id",
            "name",
            "description",
            "version",
            "algorithm",
            "algorithm_display",
            "accuracy",
            "precision",
            "recall",
            "f1_score",
            "training_samples",
            "feature_count",
            "status",
            "status_display",
            "is_active",
            "created_by_name",
            "created_at",
            "updated_at",
            "trained_at",
        ]
        read_only_fields = [
            "accuracy",
            "precision",
            "recall",
            "f1_score",
            "training_samples",
            "feature_count",
            "trained_at",
        ]


class ClassificationModelCreateSerializer(serializers.ModelSerializer):
    """分类模型创建序列化器"""

    training_dataset_id = serializers.IntegerField(write_only=True)
    test_size = serializers.FloatField(default=0.2, min_value=0.1, max_value=0.5)

    class Meta:
        model = ClassificationModel
        fields = [
            "name",
            "description",
            "version",
            "algorithm",
            "training_params",
            "training_dataset_id",
            "test_size",
        ]

    def validate_training_dataset_id(self, value):
        try:
            TrainingDataset.objects.get(id=value)
        except TrainingDataset.DoesNotExist:
            raise serializers.ValidationError("训练数据集不存在")
        return value


class TrainingDatasetSerializer(serializers.ModelSerializer):
    """训练数据集序列化器"""

    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )
    sample_count = serializers.SerializerMethodField()

    class Meta:
        model = TrainingDataset
        fields = [
            "id",
            "name",
            "description",
            "total_samples",
            "category_distribution",
            "avg_text_length",
            "min_samples_per_category",
            "sample_count",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "total_samples",
            "category_distribution",
            "avg_text_length",
            "min_samples_per_category",
        ]

    def get_sample_count(self, obj):
        return obj.samples.count()


class TrainingSampleSerializer(serializers.ModelSerializer):
    """训练样本序列化器"""

    category_name = serializers.CharField(source="category.name", read_only=True)
    source_document_title = serializers.CharField(
        source="source_document.title", read_only=True
    )
    text_preview = serializers.SerializerMethodField()

    class Meta:
        model = TrainingSample
        fields = [
            "id",
            "text",
            "text_preview",
            "category",
            "category_name",
            "source_document",
            "source_document_title",
            "text_length",
            "is_validated",
            "created_at",
        ]
        read_only_fields = ["text_length"]

    def get_text_preview(self, obj):
        return obj.text[:100] + "..." if len(obj.text) > 100 else obj.text


class TrainingSampleCreateSerializer(serializers.ModelSerializer):
    """训练样本创建序列化器"""

    class Meta:
        model = TrainingSample
        fields = ["dataset", "text", "category", "source_document", "is_validated"]


class ClassificationRuleSerializer(serializers.ModelSerializer):
    """分类规则序列化器"""

    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )
    rule_type_display = serializers.CharField(
        source="get_rule_type_display", read_only=True
    )
    target_category_name = serializers.CharField(
        source="target_category.name", read_only=True
    )

    class Meta:
        model = ClassificationRule
        fields = [
            "id",
            "name",
            "description",
            "rule_type",
            "rule_type_display",
            "pattern",
            "target_category",
            "target_category_name",
            "priority",
            "is_active",
            "match_count",
            "success_rate",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["match_count", "success_rate"]


class ClassificationRuleCreateSerializer(serializers.ModelSerializer):
    """分类规则创建序列化器"""

    class Meta:
        model = ClassificationRule
        fields = [
            "name",
            "description",
            "rule_type",
            "pattern",
            "target_category",
            "priority",
            "is_active",
        ]


class ClassificationLogSerializer(serializers.ModelSerializer):
    """分类日志序列化器"""

    document_title = serializers.CharField(source="document.title", read_only=True)
    predicted_category_name = serializers.CharField(
        source="predicted_category.name", read_only=True
    )
    actual_category_name = serializers.CharField(
        source="actual_category.name", read_only=True
    )
    executed_by_name = serializers.CharField(
        source="executed_by.username", read_only=True
    )
    method_display = serializers.CharField(source="get_method_display", read_only=True)
    model_name = serializers.CharField(source="model.name", read_only=True)
    rule_name = serializers.CharField(source="rule.name", read_only=True)

    class Meta:
        model = ClassificationLog
        fields = [
            "id",
            "document",
            "document_title",
            "predicted_category",
            "predicted_category_name",
            "actual_category",
            "actual_category_name",
            "method",
            "method_display",
            "confidence",
            "model",
            "model_name",
            "rule",
            "rule_name",
            "is_correct",
            "executed_by_name",
            "executed_at",
            "metadata",
        ]


class ClassificationStatsSerializer(serializers.Serializer):
    """分类统计序列化器"""

    total_classifications = serializers.IntegerField()
    accuracy_rate = serializers.FloatField()
    method_distribution = serializers.DictField()
    category_distribution = serializers.DictField()
    confidence_stats = serializers.DictField()
    recent_classifications = serializers.ListField()
    model_performance = serializers.DictField()
    rule_performance = serializers.DictField()


class DocumentClassificationSerializer(serializers.Serializer):
    """文档分类请求序列化器"""

    document_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)
    force_reclassify = serializers.BooleanField(default=False)
    method = serializers.ChoiceField(choices=["auto", "rule", "ml"], default="auto")


class ModelTrainingSerializer(serializers.Serializer):
    """模型训练请求序列化器"""

    dataset_id = serializers.IntegerField()
    model_name = serializers.CharField(max_length=100)
    model_version = serializers.CharField(max_length=20)
    algorithm = serializers.ChoiceField(
        choices=[
            ("naive_bayes", "朴素贝叶斯"),
            ("svm", "支持向量机"),
            ("random_forest", "随机森林"),
            ("logistic_regression", "逻辑回归"),
            ("neural_network", "神经网络"),
        ]
    )
    test_size = serializers.FloatField(default=0.2, min_value=0.1, max_value=0.5)
    training_params = serializers.DictField(default=dict)

    def validate_dataset_id(self, value):
        try:
            TrainingDataset.objects.get(id=value)
        except TrainingDataset.DoesNotExist:
            raise serializers.ValidationError("训练数据集不存在")
        return value


class ModelEvaluationSerializer(serializers.Serializer):
    """模型评估结果序列化器"""

    accuracy = serializers.FloatField()
    precision = serializers.FloatField()
    recall = serializers.FloatField()
    f1_score = serializers.FloatField()
    avg_confidence = serializers.FloatField()
    test_samples = serializers.IntegerField()
    classification_report = serializers.DictField()


class RuleTestSerializer(serializers.Serializer):
    """规则测试序列化器"""

    rule_id = serializers.IntegerField()
    test_text = serializers.CharField()

    def validate_rule_id(self, value):
        try:
            ClassificationRule.objects.get(id=value)
        except ClassificationRule.DoesNotExist:
            raise serializers.ValidationError("分类规则不存在")
        return value
