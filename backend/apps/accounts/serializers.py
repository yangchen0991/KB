"""
用户账户序列化器
"""

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User, UserActivity, UserProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "phone",
            "department",
            "position",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("密码不匹配")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        # 创建用户配置文件
        UserProfile.objects.create(user=user)
        return user


class UserLoginSerializer(serializers.Serializer):
    """用户登录序列化器"""

    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError("邮箱或密码错误")
            if not user.is_active:
                raise serializers.ValidationError("账户已被禁用")
            attrs["user"] = user
        else:
            raise serializers.ValidationError("必须提供邮箱和密码")

        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """用户配置序列化器"""

    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "avatar",
            "department",
            "position",
            "is_verified",
            "can_upload",
            "can_classify",
            "can_manage_workflows",
            "documents_uploaded",
            "last_activity",
            "date_joined",
        )
        read_only_fields = (
            "id",
            "username",
            "documents_uploaded",
            "last_activity",
            "date_joined",
        )


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """用户配置更新序列化器"""

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone",
            "avatar",
            "department",
            "position",
        )


class UserProfileSettingsSerializer(serializers.ModelSerializer):
    """用户设置序列化器"""

    class Meta:
        model = UserProfile
        fields = (
            "theme",
            "language",
            "email_notifications",
            "push_notifications",
            "default_classification",
            "auto_ocr",
        )


class UserActivitySerializer(serializers.ModelSerializer):
    """用户活动序列化器"""

    user_name = serializers.CharField(source="user.username", read_only=True)
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = UserActivity
        fields = (
            "id",
            "user_name",
            "action",
            "action_display",
            "description",
            "ip_address",
            "created_at",
        )
        read_only_fields = ("id", "user_name", "action_display", "created_at")


class PasswordChangeSerializer(serializers.Serializer):
    """密码修改序列化器"""

    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError("新密码不匹配")
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("原密码错误")
        return value


class UserListSerializer(serializers.ModelSerializer):
    """用户列表序列化器"""

    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "full_name",
            "department",
            "position",
            "is_active",
            "is_verified",
            "date_joined",
            "last_activity",
        )
