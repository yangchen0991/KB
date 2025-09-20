"""
文档分类视图
"""

from django.db.models import Avg, Count, Q, Min, Max
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, generics, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import (
    ClassificationLog,
    ClassificationModel,
    ClassificationRule,
    TrainingDataset,
    TrainingSample,
)
from .serializers import (
    ClassificationLogSerializer,
    ClassificationModelCreateSerializer,
    ClassificationModelSerializer,
    ClassificationRuleCreateSerializer,
    ClassificationRuleSerializer,
    ClassificationStatsSerializer,
    DocumentClassificationSerializer,
    ModelEvaluationSerializer,
    ModelTrainingSerializer,
    RuleTestSerializer,
    TrainingDatasetSerializer,
    TrainingSampleCreateSerializer,
    TrainingSampleSerializer,
)
from .tasks import (
    classify_documents_batch,
    evaluate_model_performance_task,
    generate_training_data,
    train_model_task,
)
from .utils import classify_document


class ClassificationModelViewSet(ModelViewSet):
    """分类模型视图集"""

    queryset = ClassificationModel.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "algorithm", "is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "accuracy", "created_at", "trained_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return ClassificationModelCreateSerializer
        return ClassificationModelSerializer

    @extend_schema(
        summary="获取分类模型列表", description="获取所有分类模型", tags=["文档分类"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="创建分类模型", description="创建新的分类模型", tags=["文档分类"]
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # 启动训练任务
            task = train_model_task.delay(
                dataset_id=serializer.validated_data["training_dataset_id"],
                model_name=serializer.validated_data["name"],
                model_version=serializer.validated_data["version"],
                algorithm=serializer.validated_data["algorithm"],
                test_size=serializer.validated_data.get("test_size", 0.2),
                training_params=serializer.validated_data.get("training_params", {}),
            )

            return Response(
                {"message": "模型训练任务已启动", "task_id": task.id},
                status=status.HTTP_202_ACCEPTED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """激活模型"""
        model = self.get_object()

        if model.status != "ready":
            return Response(
                {"error": "只能激活已就绪的模型"}, status=status.HTTP_400_BAD_REQUEST
            )

        # 取消其他模型的激活状态
        ClassificationModel.objects.filter(is_active=True).update(is_active=False)

        # 激活当前模型
        model.is_active = True
        model.save()

        return Response({"message": "模型已激活"})

    @action(detail=True, methods=["post"])
    def evaluate(self, request, pk=None):
        """评估模型性能"""
        model = self.get_object()
        test_dataset_id = request.data.get("test_dataset_id")

        # 启动评估任务
        task = evaluate_model_performance_task.delay(model.id, test_dataset_id)

        return Response({"message": "模型评估任务已启动", "task_id": task.id})

    @action(detail=False, methods=["get"])
    def active(self, request):
        """获取当前激活的模型"""
        active_model = ClassificationModel.objects.filter(is_active=True).first()
        if active_model:
            serializer = ClassificationModelSerializer(active_model)
            return Response(serializer.data)
        return Response({"message": "没有激活的模型"}, status=status.HTTP_404_NOT_FOUND)


class TrainingDatasetViewSet(ModelViewSet):
    """训练数据集视图集"""

    queryset = TrainingDataset.objects.all()
    serializer_class = TrainingDatasetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "total_samples", "created_at"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["get"])
    def samples(self, request, pk=None):
        """获取数据集样本"""
        dataset = self.get_object()
        samples = dataset.samples.all()

        # 分页
        page = self.paginate_queryset(samples)
        if page is not None:
            serializer = TrainingSampleSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TrainingSampleSerializer(samples, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def add_sample(self, request, pk=None):
        """添加训练样本"""
        dataset = self.get_object()

        data = request.data.copy()
        data["dataset"] = dataset.id

        serializer = TrainingSampleCreateSerializer(data=data)
        if serializer.is_valid():
            sample = serializer.save()

            # 更新数据集统计
            self.update_dataset_stats(dataset)

            return Response(
                TrainingSampleSerializer(sample).data, status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def generate_from_documents(self, request):
        """从文档生成训练数据"""
        task = generate_training_data.delay()

        return Response({"message": "训练数据生成任务已启动", "task_id": task.id})

    def update_dataset_stats(self, dataset):
        """更新数据集统计信息"""
        samples = dataset.samples.all()

        dataset.total_samples = samples.count()

        # 分类分布
        category_dist = samples.values("category__name").annotate(count=Count("id"))
        dataset.category_distribution = {
            item["category__name"]: item["count"] for item in category_dist
        }

        # 其他统计
        if samples.exists():
            dataset.avg_text_length = (
                samples.aggregate(avg=Avg("text_length"))["avg"] or 0
            )

            dataset.min_samples_per_category = (
                min(dataset.category_distribution.values())
                if dataset.category_distribution
                else 0
            )

        dataset.save()


class TrainingSampleViewSet(ModelViewSet):
    """训练样本视图集"""

    queryset = TrainingSample.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["dataset", "category", "is_validated"]
    search_fields = ["text"]
    ordering_fields = ["created_at", "text_length"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TrainingSampleCreateSerializer
        return TrainingSampleSerializer


class ClassificationRuleViewSet(ModelViewSet):
    """分类规则视图集"""

    queryset = ClassificationRule.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["rule_type", "target_category", "is_active"]
    search_fields = ["name", "description", "pattern"]
    ordering_fields = ["name", "priority", "success_rate", "created_at"]
    ordering = ["-priority", "name"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ClassificationRuleCreateSerializer
        return ClassificationRuleSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        """测试规则"""
        rule = self.get_object()
        test_text = request.data.get("test_text", "")

        if not test_text:
            return Response(
                {"error": "请提供测试文本"}, status=status.HTTP_400_BAD_REQUEST
            )

        # 创建临时文档对象进行测试
        class MockDocument:
            def __init__(self, text):
                self.title = text[:100]
                self.description = ""
                self.ocr_text = text
                self.file_type = "txt"
                self.file = type("MockFile", (), {"name": "test.txt"})()

        mock_doc = MockDocument(test_text)
        is_match = rule.match(mock_doc)

        return Response(
            {
                "is_match": is_match,
                "rule_name": rule.name,
                "target_category": rule.target_category.name if is_match else None,
            }
        )


class ClassificationLogViewSet(generics.ListAPIView):
    """分类日志视图"""

    queryset = ClassificationLog.objects.all()
    serializer_class = ClassificationLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["method", "is_correct", "model", "rule"]
    ordering_fields = ["executed_at", "confidence"]
    ordering = ["-executed_at"]


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@extend_schema(
    summary="批量分类文档", description="对指定文档执行批量分类", tags=["文档分类"]
)
def classify_documents(request):
    """批量分类文档"""
    serializer = DocumentClassificationSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    document_ids = data["document_ids"]
    force_reclassify = data.get("force_reclassify", False)

    # 启动批量分类任务
    task = classify_documents_batch.delay(document_ids, force_reclassify)

    return Response(
        {
            "message": "批量分类任务已启动",
            "task_id": task.id,
            "document_count": len(document_ids),
        }
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
@extend_schema(
    summary="获取分类统计信息", description="获取文档分类的统计数据", tags=["文档分类"]
)
def classification_stats(request):
    """获取分类统计信息"""
    # 基础统计
    total_classifications = ClassificationLog.objects.count()
    correct_classifications = ClassificationLog.objects.filter(is_correct=True).count()
    accuracy_rate = (
        correct_classifications / total_classifications
        if total_classifications > 0
        else 0
    )

    # 方法分布
    method_stats = ClassificationLog.objects.values("method").annotate(
        count=Count("id")
    )
    method_distribution = {item["method"]: item["count"] for item in method_stats}

    # 分类分布
    category_stats = ClassificationLog.objects.values(
        "predicted_category__name"
    ).annotate(count=Count("id"))
    category_distribution = {
        item["predicted_category__name"]: item["count"] for item in category_stats
    }

    # 置信度统计
    confidence_stats = ClassificationLog.objects.aggregate(
        avg_confidence=Avg("confidence"),
        min_confidence=Min("confidence"),
        max_confidence=Max("confidence"),
    )

    # 最近分类
    recent_logs = ClassificationLog.objects.order_by("-executed_at")[:10]
    recent_classifications = ClassificationLogSerializer(recent_logs, many=True).data

    # 模型性能
    model_stats = ClassificationModel.objects.filter(is_active=True).values(
        "name", "accuracy", "precision", "recall", "f1_score"
    )
    model_performance = list(model_stats)

    # 规则性能
    rule_stats = (
        ClassificationRule.objects.filter(is_active=True)
        .values("name", "success_rate", "match_count")
        .order_by("-success_rate")[:10]
    )
    rule_performance = list(rule_stats)

    stats_data = {
        "total_classifications": total_classifications,
        "accuracy_rate": accuracy_rate,
        "method_distribution": method_distribution,
        "category_distribution": category_distribution,
        "confidence_stats": confidence_stats,
        "recent_classifications": recent_classifications,
        "model_performance": model_performance,
        "rule_performance": rule_performance,
    }

    serializer = ClassificationStatsSerializer(stats_data)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@extend_schema(
    summary="训练新模型",
    description="使用指定数据集训练新的分类模型",
    tags=["文档分类"],
)
def train_model(request):
    """训练新模型"""
    serializer = ModelTrainingSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    # 启动训练任务
    task = train_model_task.delay(
        dataset_id=data["dataset_id"],
        model_name=data["model_name"],
        model_version=data["model_version"],
        algorithm=data["algorithm"],
        test_size=data.get("test_size", 0.2),
        training_params=data.get("training_params", {}),
    )

    return Response({"message": "模型训练任务已启动", "task_id": task.id})
