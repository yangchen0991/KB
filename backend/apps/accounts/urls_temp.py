"""
用户账户URL配置 - 临时简化版本
"""

from django.http import JsonResponse
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


def accounts_root(request):
    """账户API根视图"""
    return JsonResponse(
        {
            "message": "用户管理API",
            "version": "1.0.0",
            "endpoints": {
                "token": "/api/accounts/token/",
                "token_refresh": "/api/accounts/token/refresh/",
            },
            "status": "active",
        }
    )


app_name = "accounts"

urlpatterns = [
    # API根目录
    path("", accounts_root, name="accounts_root"),
    # JWT认证端点
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
