"""
用户账户URL配置
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

app_name = "accounts"

urlpatterns = [
    # 认证相关
    path("register/", views.UserRegistrationView.as_view(), name="register"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # 用户资料
    path("profile/", views.UserProfileView.as_view(), name="profile"),
    path("settings/", views.UserSettingsView.as_view(), name="settings"),
    path(
        "password/change/", views.PasswordChangeView.as_view(), name="password_change"
    ),
    # 用户活动
    path("activities/", views.UserActivityView.as_view(), name="activities"),
    path("stats/", views.user_stats, name="stats"),
    # 用户管理
    path("users/", views.UserListView.as_view(), name="user_list"),
    # 工具接口
    path("check-email/", views.check_email_availability, name="check_email"),
    path("check-username/", views.check_username_availability, name="check_username"),
]
