"""
文档分类URL配置
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "classification"

router = DefaultRouter()
router.register(r"models", views.ClassificationModelViewSet)
router.register(r"datasets", views.TrainingDatasetViewSet)
router.register(r"samples", views.TrainingSampleViewSet)
router.register(r"rules", views.ClassificationRuleViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("logs/", views.ClassificationLogViewSet.as_view(), name="classification_logs"),
    path("classify/", views.classify_documents, name="classify_documents"),
    path("stats/", views.classification_stats, name="classification_stats"),
    path("train/", views.train_model, name="train_model"),
]
