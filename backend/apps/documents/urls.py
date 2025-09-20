"""
文档模块URL配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# 创建路由器
router = DefaultRouter()

# 注册视图集
router.register(r'documents', views.DocumentViewSet, basename='document')
router.register(r'categories', views.CategoryViewSet, basename='category')

app_name = 'documents'

urlpatterns = [
    # API路由 - 直接包含路由器URL，不再嵌套api/
    path('', include(router.urls)),
    
    # 基础API路由 - 使用现有的视图
    # 其他高级功能将在后续添加
]