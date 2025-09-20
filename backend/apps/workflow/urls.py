from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"templates", views.WorkflowTemplateViewSet)
router.register(r"executions", views.WorkflowExecutionViewSet)
router.register(r"node-executions", views.NodeExecutionViewSet)
router.register(r"schedules", views.WorkflowScheduleViewSet)
router.register(r"variables", views.WorkflowVariableViewSet)
router.register(r"nodes", views.WorkflowNodeViewSet, basename="workflow-node")

app_name = "workflow"

urlpatterns = [
    path("", include(router.urls)),
]
