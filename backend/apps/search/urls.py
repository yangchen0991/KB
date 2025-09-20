"""
搜索模块URL配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# 创建路由器
router = DefaultRouter()

# 注册视图集
router.register(r'search', views.SearchViewSet, basename='search')

app_name = 'search'

urlpatterns = [
    # API路由
    path('', include(router.urls)),
]