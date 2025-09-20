"""
文档分类工具函数
"""

import logging
import re

import numpy as np
from django.conf import settings
from django.db import models
from django.utils import timezone
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    precision_recall_fscore_support,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC

from .models import (
    ClassificationLog,
    ClassificationModel,
    ClassificationRule,
    TrainingSample,
)

logger = logging.getLogger(__name__)


def preprocess_text(text):
    """文本预处理"""
    if not text:
        return ""

    # 转换为小写
    text = text.lower()

    # 移除特殊字符，保留中文、英文、数字和空格
    text = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9\s]", " ", text)

    # 移除多余空格
    text = re.sub(r"\s+", " ", text).strip()

    return text


def extract_features(document):
    """提取文档特征"""
    features = {}

    # 文本特征
    text_content = f"{document.title} {document.description} {document.ocr_text}"
    features["text"] = preprocess_text(text_content)
    features["text_length"] = len(text_content)
    features["word_count"] = len(text_content.split())

    # 文件特征
    features["file_type"] = document.file_type.lower()
    features["file_size"] = document.file_size
    features["page_count"] = document.page_count

    # OCR特征
    features["has_ocr"] = bool(document.ocr_text)
    features["ocr_confidence"] = document.ocr_confidence

    return features


def classify_by_rules(document):
    """基于规则的分类"""
    active_rules = ClassificationRule.objects.filter(is_active=True).order_by(
        "-priority"
    )

    for rule in active_rules:
        if rule.match(document):
            # 更新规则统计
            rule.match_count += 1
            rule.save(update_fields=["match_count"])

            logger.info(f"Document {document.id} matched rule: {rule.name}")
            return rule.target_category, 1.0, rule

    return None, 0.0, None


def classify_by_ml(document):
    """基于机器学习的分类"""
    try:
        # 获取活跃的模型
        active_model = ClassificationModel.objects.filter(
            is_active=True, status="ready"
        ).first()

        if not active_model:
            logger.warning("No active ML model found")
            return None, 0.0, None

        # 加载模型和向量化器
        model = active_model.load_model()
        vectorizer = active_model.load_vectorizer()

        if not model or not vectorizer:
            logger.error(f"Failed to load model {active_model.name}")
            return None, 0.0, None

        # 提取特征
        features = extract_features(document)
        text_features = vectorizer.transform([features["text"]])

        # 预测
        prediction = model.predict(text_features)[0]
        probabilities = model.predict_proba(text_features)[0]
        confidence = max(probabilities)

        # 获取预测的分类
        from apps.documents.models import Category

        try:
            predicted_category = Category.objects.get(id=prediction)
            logger.info(
                f"ML prediction for document {document.id}: {predicted_category.name} (confidence: {confidence:.2f})"
            )
            return predicted_category, confidence, active_model
        except Category.DoesNotExist:
            logger.error(f"Predicted category {prediction} not found")
            return None, 0.0, None

    except Exception as e:
        logger.error(f"ML classification error: {str(e)}")
        return None, 0.0, None


def classify_document(document):
    """文档分类主函数"""
    # 首先尝试规则分类
    rule_category, rule_confidence, rule = classify_by_rules(document)

    # 然后尝试机器学习分类
    ml_category, ml_confidence, model = classify_by_ml(document)

    # 选择最佳分类结果
    final_category = None
    final_confidence = 0.0
    method = "manual"
    used_model = None
    used_rule = None

    if rule_category and ml_category:
        # 如果两种方法都有结果，选择置信度更高的
        if rule_confidence >= ml_confidence:
            final_category = rule_category
            final_confidence = rule_confidence
            method = "rule"
            used_rule = rule
        else:
            final_category = ml_category
            final_confidence = ml_confidence
            method = "ml"
            used_model = model
    elif rule_category:
        final_category = rule_category
        final_confidence = rule_confidence
        method = "rule"
        used_rule = rule
    elif ml_category:
        final_category = ml_category
        final_confidence = ml_confidence
        method = "ml"
        used_model = model

    # 记录分类日志
    if final_category:
        ClassificationLog.objects.create(
            document=document,
            predicted_category=final_category,
            method=method,
            confidence=final_confidence,
            model=used_model,
            rule=used_rule,
            executed_by_id=1,  # 系统用户
            metadata={
                "rule_confidence": rule_confidence,
                "ml_confidence": ml_confidence,
            },
        )

    return final_category


def train_classification_model(
    dataset_id, algorithm="naive_bayes", test_size=0.2, **params
):
    """训练分类模型"""
    try:
        from .models import TrainingDataset

        dataset = TrainingDataset.objects.get(id=dataset_id)

        # 获取训练样本
        samples = TrainingSample.objects.filter(dataset=dataset, is_validated=True)

        if samples.count() < settings.ML_MIN_TRAINING_SAMPLES:
            raise ValueError(
                f"训练样本不足，至少需要 {settings.ML_MIN_TRAINING_SAMPLES} 个样本"
            )

        # 准备数据
        texts = []
        labels = []

        for sample in samples:
            texts.append(preprocess_text(sample.text))
            labels.append(sample.category.id)

        # 文本向量化
        vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 2),
            stop_words=None,  # 中文没有内置停用词
            min_df=2,
            max_df=0.95,
        )

        X = vectorizer.fit_transform(texts)
        y = np.array(labels)

        # 分割训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        # 选择算法
        if algorithm == "naive_bayes":
            model = MultinomialNB(**params)
        elif algorithm == "svm":
            model = SVC(probability=True, **params)
        elif algorithm == "random_forest":
            model = RandomForestClassifier(**params)
        elif algorithm == "logistic_regression":
            model = LogisticRegression(**params)
        elif algorithm == "neural_network":
            model = MLPClassifier(**params)
        else:
            raise ValueError(f"不支持的算法: {algorithm}")

        # 训练模型
        model.fit(X_train, y_train)

        # 评估模型
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average="weighted"
        )

        # 交叉验证
        cv_scores = cross_val_score(model, X_train, y_train, cv=5)

        logger.info(f"Model training completed:")
        logger.info(f"Accuracy: {accuracy:.4f}")
        logger.info(f"Precision: {precision:.4f}")
        logger.info(f"Recall: {recall:.4f}")
        logger.info(f"F1-score: {f1:.4f}")
        logger.info(f"CV Score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

        # 检查性能阈值
        if (
            accuracy < settings.ML_ACCURACY_THRESHOLD
            or recall < settings.ML_RECALL_THRESHOLD
        ):
            logger.warning(
                f"Model performance below threshold (accuracy: {accuracy:.4f}, recall: {recall:.4f})"
            )

        return {
            "model": model,
            "vectorizer": vectorizer,
            "metrics": {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "cv_mean": cv_scores.mean(),
                "cv_std": cv_scores.std(),
            },
            "training_info": {
                "algorithm": algorithm,
                "training_samples": len(X_train),
                "test_samples": len(X_test),
                "feature_count": X.shape[1],
                "params": params,
            },
        }

    except Exception as e:
        logger.error(f"Model training failed: {str(e)}")
        raise


def evaluate_model_performance(model_id, test_dataset_id=None):
    """评估模型性能"""
    try:
        model_obj = ClassificationModel.objects.get(id=model_id)
        model = model_obj.load_model()
        vectorizer = model_obj.load_vectorizer()

        if not model or not vectorizer:
            raise ValueError("无法加载模型或向量化器")

        # 获取测试数据
        if test_dataset_id:
            from .models import TrainingDataset

            test_dataset = TrainingDataset.objects.get(id=test_dataset_id)
            test_samples = TrainingSample.objects.filter(
                dataset=test_dataset, is_validated=True
            )
        else:
            # 使用最近的分类日志作为测试数据
            test_logs = ClassificationLog.objects.filter(
                model=model_obj, actual_category__isnull=False
            )[:1000]

            if not test_logs:
                raise ValueError("没有可用的测试数据")

        # 准备测试数据
        if test_dataset_id:
            texts = [preprocess_text(sample.text) for sample in test_samples]
            true_labels = [sample.category.id for sample in test_samples]
        else:
            from apps.documents.models import Document

            texts = []
            true_labels = []

            for log in test_logs:
                document = log.document
                text_content = (
                    f"{document.title} {document.description} {document.ocr_text}"
                )
                texts.append(preprocess_text(text_content))
                true_labels.append(log.actual_category.id)

        # 预测
        X_test = vectorizer.transform(texts)
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)

        # 计算指标
        accuracy = accuracy_score(true_labels, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(
            true_labels, y_pred, average="weighted"
        )

        # 置信度分析
        confidences = [max(proba) for proba in y_pred_proba]
        avg_confidence = np.mean(confidences)

        # 分类报告
        from apps.documents.models import Category

        category_names = [
            Category.objects.get(id=cat_id).name for cat_id in set(true_labels)
        ]
        report = classification_report(
            true_labels, y_pred, target_names=category_names, output_dict=True
        )

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "avg_confidence": avg_confidence,
            "classification_report": report,
            "test_samples": len(texts),
        }

    except Exception as e:
        logger.error(f"Model evaluation failed: {str(e)}")
        raise


def update_rule_performance():
    """更新规则性能统计"""
    rules = ClassificationRule.objects.filter(is_active=True)

    for rule in rules:
        # 获取使用该规则的分类日志
        logs = ClassificationLog.objects.filter(rule=rule)

        if logs.exists():
            correct_count = logs.filter(is_correct=True).count()
            total_count = logs.count()
            success_rate = correct_count / total_count if total_count > 0 else 0.0

            rule.success_rate = success_rate
            rule.save(update_fields=["success_rate"])

            logger.info(f"Updated rule {rule.name} success rate: {success_rate:.2f}")


def generate_training_data_from_documents():
    """从已分类文档生成训练数据"""
    from apps.documents.models import Category, Document

    from .models import TrainingDataset, TrainingSample

    # 创建数据集
    dataset = TrainingDataset.objects.create(
        name=f"Auto-generated Dataset {timezone.now().strftime('%Y%m%d_%H%M%S')}",
        description="从已分类文档自动生成的训练数据集",
    )

    # 获取已分类的文档
    categorized_docs = Document.objects.filter(
        category__isnull=False, status="completed"
    ).exclude(ocr_text="")

    category_counts = {}

    for doc in categorized_docs:
        # 提取文本
        text_content = f"{doc.title}\n{doc.description}\n{doc.ocr_text}"

        if len(text_content.strip()) < 50:  # 跳过太短的文本
            continue

        # 创建训练样本
        sample = TrainingSample.objects.create(
            dataset=dataset,
            text=text_content,
            category=doc.category,
            source_document=doc,
            is_validated=True,
        )

        # 统计分类分布
        category_name = doc.category.name
        category_counts[category_name] = category_counts.get(category_name, 0) + 1

    # 更新数据集统计
    dataset.total_samples = dataset.samples.count()
    dataset.category_distribution = category_counts
    dataset.min_samples_per_category = (
        min(category_counts.values()) if category_counts else 0
    )
    dataset.avg_text_length = (
        dataset.samples.aggregate(avg_length=models.Avg("text_length"))["avg_length"]
        or 0
    )
    dataset.save()

    logger.info(f"Generated training dataset with {dataset.total_samples} samples")
    return dataset
