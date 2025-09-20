"""
开发环境URL配置
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # API v1 Routes
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/documents/", include("apps.documents.urls")),
    path("api/v1/search/", include("apps.search.urls")),
    path("api/v1/workflow/", include("apps.workflow.urls")),
    path("api/v1/monitoring/", include("apps.monitoring.urls")),
    path("api/v1/ocr/", include("apps.ocr.urls")),
]

# 开发环境静态文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
