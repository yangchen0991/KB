"""
开发环境URL配置 - 完整版本
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def api_root(request):
    """API根视图"""
    return JsonResponse(
        {
            "message": "知识库管理系统 API",
            "version": "1.0.0",
            "endpoints": {
                "admin": "/admin/",
                "api": "/api/",
                "accounts": "/api/accounts/",
                "documents": "/api/documents/",
                "classification": "/api/classification/",
                "monitoring": "/api/monitoring/",
            },
        }
    )


urlpatterns = [
    # API根目录
    path("", api_root, name="api_root"),
    # 管理后台
    path("admin/", admin.site.urls),
    # API路由
    path(
        "api/",
        include(
            [
                path("accounts/", include("apps.accounts.urls")),
                path("documents/", include("apps.documents.urls")),
                path("classification/", include("apps.classification.urls")),
                path("monitoring/", include("apps.monitoring.urls")),
            ]
        ),
    ),
]

# 开发环境静态文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
