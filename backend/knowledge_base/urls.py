"""
Knowledge Base URL Configuration - 最终静态文件修复版本
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from apps.core.views import home_view, api_status

urlpatterns = [
    # Home page
    path("", home_view, name='home'),
    path("api/status/", api_status, name='api_status'),
    # Admin
    path("admin/", admin.site.urls),
    # API Routes
    path("api/v1/auth/", include("apps.accounts.urls")),
    path('api/v1/documents/', include('apps.documents.urls')),
    path('api/v1/search/', include('apps.search.urls')),
    path('api/v1/monitoring/', include('apps.monitoring.urls')),
    path('api/v1/ocr/', include('apps.ocr.urls')),
]

# 静态文件和媒体文件服务 - 开发环境
if settings.DEBUG:
    from django.conf.urls.static import static
    from django.views.static import serve
    from django.urls import re_path
    import os
    
    # 标准静态文件服务
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # 备用静态文件服务路径
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {
            'document_root': settings.STATIC_ROOT,
            'show_indexes': True,
        }),
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
            'show_indexes': True,
        }),
    ]