"""
Knowledge Base URL Configuration
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API Documentation (暂时禁用)
    # path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # API Routes - Phase 1: 用户认证
    path("api/v1/auth/", include("apps.accounts.urls")),
    # API Routes - 已启用模块
    path('api/v1/documents/', include('apps.documents.urls')),      # Phase 2
    # path('api/v1/classification/', include('apps.classification.urls')),  # Phase 3
    path('api/v1/search/', include('apps.search.urls')),           # Phase 3
    # path('api/v1/workflows/', include('apps.workflows.urls')),     # Phase 4
    path('api/v1/monitoring/', include('apps.monitoring.urls')),   # Phase 4
    # Prometheus metrics (暂时禁用)
    # path('metrics/', include('django_prometheus.urls')),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # 添加静态文件服务的备用路径
    from django.views.static import serve
    from django.urls import re_path
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    ]
