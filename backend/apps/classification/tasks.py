"""
文档分类异步任务
"""

import logging

from celery import shared_task
from django.utils import timezone

from .models import ClassificationLog, ClassificationModel, TrainingDataset
from .serializers import ModelTrainingSerializer
from .utils import (
    classify_document,
    train_classification_model,
    update_rule_performance,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def train_model_task(
    self,
    dataset_id,
    model_name,
    model_version,
    algorithm,
    test_size=0.2,
    training_params=None,
):
    """训练分类模型任务"""
    try:
        # 创建模型记录
        model_obj = ClassificationModel.objects.create(
            name=model_name,
            version=model_version,
            algorithm=algorithm,
            training_params=training_params or {},
            status="training",
            created_by_id=1,  # 系统用户
        )

        # 更新任务状态
        self.update_state(state="PROGRESS", meta={"progress": 10, "status": "开始训练"})

        # 训练模型
        result = train_classification_model(
            dataset_id=dataset_id,
            algorithm=algorithm,
            test_size=test_size,
            **training_params or {},
        )

        # 更新任务状态
        self.update_state(state="PROGRESS", meta={"progress": 80, "status": "保存模型"})

        # 保存模型和向量化器
        model_obj.save_model(result["model"], result["vectorizer"])

        # 更新模型信息
        metrics = result["metrics"]
        training_info = result["training_info"]

        model_obj.accuracy = metrics["accuracy"]
        model_obj.precision = metrics["precision"]
        model_obj.recall = metrics["recall"]
        model_obj.f1_score = metrics["f1_score"]
        model_obj.training_samples = training_info["training_samples"]
        model_obj.feature_count = training_info["feature_count"]
        model_obj.status = "ready"
        model_obj.trained_at = timezone.now()
        model_obj.save()

        logger.info(
            f"Model {model_name} v{model_version} training completed successfully"
        )

        return {
            "status": "completed",
            "model_id": model_obj.id,
            "metrics": metrics,
            "training_info": training_info,
        }

    except Exception as e:
        logger.error(f"Model training failed: {str(e)}")

        # 更新模型状态为失败
        if "model_obj" in locals():
            model_obj.status = "failed"
            model_obj.save()

        return {"status": "error", "message": str(e)}


@shared_task
def classify_documents_batch(document_ids, force_reclassify=False):
    """批量分类文档"""
    from apps.documents.models import Document

    results = []

    for doc_id in document_ids:
        try:
            document = Document.objects.get(id=doc_id)

            # 检查是否需要重新分类
            if not force_reclassify and document.category:
                results.append(
                    {
                        "document_id": doc_id,
                        "status": "skipped",
                        "message": "文档已有分类",
                    }
                )
                continue

            # 执行分类
            predicted_category = classify_document(document)

            if predicted_category:
                document.category = predicted_category
                document.save()

                results.append(
                    {
                        "document_id": doc_id,
                        "status": "success",
                        "category": predicted_category.name,
                    }
                )
            else:
                results.append(
                    {
                        "document_id": doc_id,
                        "status": "failed",
                        "message": "无法确定分类",
                    }
                )

        except Document.DoesNotExist:
            results.append(
                {"document_id": doc_id, "status": "error", "message": "文档不存在"}
            )
        except Exception as e:
            logger.error(f"Error classifying document {doc_id}: {str(e)}")
            results.append(
                {"document_id": doc_id, "status": "error", "message": str(e)}
            )

    return results


@shared_task
def update_ml_models():
    """更新机器学习模型"""
    try:
        # 更新规则性能统计
        update_rule_performance()

        # 检查是否需要重新训练模型
        active_models = ClassificationModel.objects.filter(
            is_active=True, status="ready"
        )

        for model in active_models:
            # 检查模型性能
            recent_logs = ClassificationLog.objects.filter(
                model=model,
                executed_at__gte=timezone.now() - timezone.timedelta(days=30),
            )

            if recent_logs.exists():
                correct_count = recent_logs.filter(is_correct=True).count()
                total_count = recent_logs.count()
                current_accuracy = correct_count / total_count

                # 如果性能下降超过阈值，标记需要重新训练
                if current_accuracy < model.accuracy * 0.9:  # 性能下降10%
                    logger.warning(
                        f"Model {model.name} performance degraded: {current_accuracy:.4f}"
                    )
                    # 这里可以触发重新训练或发送通知

        logger.info("ML models update completed")

    except Exception as e:
        logger.error(f"Error updating ML models: {str(e)}")


@shared_task
def generate_training_data():
    """生成训练数据"""
    try:
        from .utils import generate_training_data_from_documents

        dataset = generate_training_data_from_documents()

        logger.info(f"Generated training dataset: {dataset.name}")
        return {
            "status": "success",
            "dataset_id": dataset.id,
            "total_samples": dataset.total_samples,
        }

    except Exception as e:
        logger.error(f"Error generating training data: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task
def evaluate_model_performance_task(model_id, test_dataset_id=None):
    """评估模型性能任务"""
    try:
        from .utils import evaluate_model_performance

        result = evaluate_model_performance(model_id, test_dataset_id)

        # 更新模型性能指标
        model = ClassificationModel.objects.get(id=model_id)
        model.accuracy = result["accuracy"]
        model.precision = result["precision"]
        model.recall = result["recall"]
        model.f1_score = result["f1_score"]
        model.save()

        logger.info(f"Model {model.name} evaluation completed")
        return result

    except Exception as e:
        logger.error(f"Error evaluating model {model_id}: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task
def cleanup_old_models():
    """清理旧模型文件"""
    try:
        import os

        from django.conf import settings

        # 获取已弃用的模型
        deprecated_models = ClassificationModel.objects.filter(status="deprecated")

        for model in deprecated_models:
            # 删除模型文件
            if model.model_file and os.path.exists(model.model_file.path):
                os.remove(model.model_file.path)
                logger.info(f"Removed model file: {model.model_file.path}")

            # 删除向量化器文件
            if model.vectorizer_file and os.path.exists(model.vectorizer_file.path):
                os.remove(model.vectorizer_file.path)
                logger.info(f"Removed vectorizer file: {model.vectorizer_file.path}")

            # 删除模型记录
            model.delete()

        logger.info("Old models cleanup completed")

    except Exception as e:
        logger.error(f"Error cleaning up old models: {str(e)}")


@shared_task
def auto_classify_new_documents():
    """自动分类新文档"""
    from apps.documents.models import Document

    try:
        # 获取未分类的已完成处理的文档
        unclassified_docs = Document.objects.filter(
            category__isnull=True, status="completed"
        )[
            :100
        ]  # 限制批量处理数量

        classified_count = 0

        for document in unclassified_docs:
            predicted_category = classify_document(document)

            if predicted_category:
                document.category = predicted_category
                document.save()
                classified_count += 1

        logger.info(f"Auto-classified {classified_count} documents")
        return {"classified_count": classified_count}

    except Exception as e:
        logger.error(f"Error in auto-classification: {str(e)}")
        return {"status": "error", "message": str(e)}
