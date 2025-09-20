"""
用户账户视图
"""

from django.contrib.auth import login, logout
from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, UserActivity, UserProfile
from .serializers import (
    PasswordChangeSerializer,
    UserActivitySerializer,
    UserListSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserProfileSettingsSerializer,
    UserProfileUpdateSerializer,
    UserRegistrationSerializer,
)


def get_client_ip(request):
    """获取客户端IP地址"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def log_user_activity(user, action, description="", request=None):
    """记录用户活动"""
    UserActivity.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
    )


class UserRegistrationView(APIView):
    """用户注册"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            log_user_activity(user, "register", "用户注册", request)

            # 生成JWT Token
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "message": "注册成功",
                    "user": UserProfileSerializer(user).data,
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """用户登录"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]

            # 更新最后活动时间
            user.last_activity = timezone.now()
            user.save(update_fields=["last_activity"])

            # 记录登录活动
            log_user_activity(user, "login", "用户登录", request)

            # 生成JWT Token
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "message": "登录成功",
                    "user": UserProfileSerializer(user).data,
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutView(APIView):
    """用户登出"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            log_user_activity(request.user, "logout", "用户登出", request)

            return Response({"message": "登出成功"})
        except Exception as e:
            return Response({"error": "登出失败"}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(RetrieveUpdateAPIView):
    """用户配置文件"""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return UserProfileSerializer
        return UserProfileUpdateSerializer

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        serializer.save()
        log_user_activity(
            self.request.user, "profile_update", "更新个人资料", self.request
        )


class UserSettingsView(RetrieveUpdateAPIView):
    """用户设置"""

    serializer_class = UserProfileSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def perform_update(self, serializer):
        serializer.save()
        log_user_activity(
            self.request.user, "settings_update", "更新用户设置", self.request
        )


class PasswordChangeView(APIView):
    """密码修改"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data["new_password"])
            user.save()

            log_user_activity(user, "password_change", "修改密码", request)

            return Response({"message": "密码修改成功"})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserActivityView(ListAPIView):
    """用户活动记录"""

    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )


class UserListView(ListAPIView):
    """用户列表（管理员）"""

    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 只有管理员可以查看所有用户
        if not self.request.user.is_staff:
            return User.objects.filter(id=self.request.user.id)

        queryset = User.objects.all()

        # 搜索功能
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(department__icontains=search)
            )

        # 部门筛选
        department = self.request.query_params.get("department")
        if department:
            queryset = queryset.filter(department=department)

        # 状态筛选
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        return queryset.order_by("-date_joined")


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """用户统计信息"""
    user = request.user

    # 获取用户统计数据
    stats = {
        "documents_uploaded": user.documents_uploaded,
        "activities_count": UserActivity.objects.filter(user=user).count(),
        "last_login": user.last_login,
        "member_since": user.date_joined,
        "permissions": {
            "can_upload": user.can_upload,
            "can_classify": user.can_classify,
            "can_manage_workflows": user.can_manage_workflows,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        },
    }

    return Response(stats)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def check_email_availability(request):
    """检查邮箱是否可用"""
    email = request.data.get("email")
    if not email:
        return Response({"error": "邮箱不能为空"}, status=status.HTTP_400_BAD_REQUEST)

    exists = User.objects.filter(email=email).exists()
    return Response(
        {
            "available": not exists,
            "message": "邮箱可用" if not exists else "邮箱已被使用",
        }
    )


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def check_username_availability(request):
    """检查用户名是否可用"""
    username = request.data.get("username")
    if not username:
        return Response({"error": "用户名不能为空"}, status=status.HTTP_400_BAD_REQUEST)

    exists = User.objects.filter(username=username).exists()
    return Response(
        {
            "available": not exists,
            "message": "用户名可用" if not exists else "用户名已被使用",
        }
    )
