"""
开发环境URL配置 - 简化版本
暂时只包含基础功能，避免复杂依赖
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import include, path


def api_root(request):
    """API根视图"""
    return JsonResponse(
        {
            "message": "知识库管理系统 API",
            "version": "1.0.0",
            "status": "running",
            "features": {
                "admin": "管理后台已启用",
                "accounts": "用户系统已启用",
                "documents": "文档管理已启用",
                "classification": "智能分类已启用",
                "monitoring": "系统监控已启用",
            },
            "endpoints": {
                "admin": "/admin/",
                "api_root": "/",
                "api_test": "/test/",
                "accounts": "/api/accounts/",
                "documents": "/api/documents/",
            },
        }
    )


def api_test(request):
    """API测试页面"""
    return render(request, "api_test.html")


urlpatterns = [
    # API根目录
    path("", api_root, name="api_root"),
    # API测试页面
    path("test/", api_test, name="api_test"),
    # 管理后台
    path("admin/", admin.site.urls),
    # API路由
    path(
        "api/",
        include(
            [
                path("accounts/", include("apps.accounts.urls_temp")),
                path("documents/", include("apps.documents.urls")),
            ]
        ),
    ),
]

# 开发环境静态文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
