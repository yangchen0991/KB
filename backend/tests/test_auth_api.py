"""
用户认证API测试用例
Phase 1: 用户认证模块测试
"""

import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class AuthAPITestCase(APITestCase):
    """用户认证API测试"""

    def setUp(self):
        """测试前准备"""
        self.register_url = reverse("accounts:register")
        self.login_url = reverse("accounts:login")
        self.refresh_url = reverse("accounts:token_refresh")
        self.profile_url = reverse("accounts:profile")

        # 创建测试用户
        self.test_user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123!",
            "first_name": "测试",
            "last_name": "用户",
        }

        self.existing_user = User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="ExistingPass123!",
        )

    def test_user_registration_success(self):
        """测试用户注册成功"""
        response = self.client.post(
            self.register_url, self.test_user_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertIn("tokens", response.data)
        self.assertEqual(
            response.data["user"]["username"], self.test_user_data["username"]
        )
        self.assertEqual(response.data["user"]["email"], self.test_user_data["email"])

        # 验证用户已创建
        self.assertTrue(
            User.objects.filter(username=self.test_user_data["username"]).exists()
        )

    def test_user_registration_duplicate_username(self):
        """测试重复用户名注册失败"""
        duplicate_data = self.test_user_data.copy()
        duplicate_data["username"] = self.existing_user.username

        response = self.client.post(self.register_url, duplicate_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_user_registration_duplicate_email(self):
        """测试重复邮箱注册失败"""
        duplicate_data = self.test_user_data.copy()
        duplicate_data["email"] = self.existing_user.email

        response = self.client.post(self.register_url, duplicate_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_user_registration_invalid_password(self):
        """测试弱密码注册失败"""
        weak_password_data = self.test_user_data.copy()
        weak_password_data["password"] = "123"

        response = self.client.post(
            self.register_url, weak_password_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_user_login_success(self):
        """测试用户登录成功"""
        login_data = {
            "username": self.existing_user.username,
            "password": "ExistingPass123!",
        }

        response = self.client.post(self.login_url, login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)

    def test_user_login_invalid_credentials(self):
        """测试错误凭据登录失败"""
        invalid_data = {
            "username": self.existing_user.username,
            "password": "wrongpassword",
        }

        response = self.client.post(self.login_url, invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_login_nonexistent_user(self):
        """测试不存在用户登录失败"""
        nonexistent_data = {"username": "nonexistentuser", "password": "somepassword"}

        response = self.client.post(self.login_url, nonexistent_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh_success(self):
        """测试Token刷新成功"""
        # 获取refresh token
        refresh = RefreshToken.for_user(self.existing_user)

        refresh_data = {"refresh": str(refresh)}

        response = self.client.post(self.refresh_url, refresh_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_token_refresh_invalid_token(self):
        """测试无效Token刷新失败"""
        invalid_refresh_data = {"refresh": "invalid_token"}

        response = self.client.post(
            self.refresh_url, invalid_refresh_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_with_valid_token(self):
        """测试有效Token访问受保护端点"""
        # 获取access token
        refresh = RefreshToken.for_user(self.existing_user)
        access_token = refresh.access_token

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.existing_user.username)

    def test_protected_endpoint_without_token(self):
        """测试无Token访问受保护端点失败"""
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_with_invalid_token(self):
        """测试无效Token访问受保护端点失败"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_profile_update(self):
        """测试用户资料更新"""
        # 认证用户
        refresh = RefreshToken.for_user(self.existing_user)
        access_token = refresh.access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        update_data = {
            "first_name": "更新的名字",
            "last_name": "更新的姓氏",
            "phone": "13800138000",
        }

        response = self.client.patch(self.profile_url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], update_data["first_name"])
        self.assertEqual(response.data["last_name"], update_data["last_name"])

        # 验证数据库中的更新
        updated_user = User.objects.get(id=self.existing_user.id)
        self.assertEqual(updated_user.first_name, update_data["first_name"])
        self.assertEqual(updated_user.last_name, update_data["last_name"])


class UserModelTestCase(TestCase):
    """用户模型测试"""

    def test_create_user(self):
        """测试创建普通用户"""
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """测试创建超级用户"""
        admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )

        self.assertEqual(admin_user.username, "admin")
        self.assertEqual(admin_user.email, "admin@example.com")
        self.assertTrue(admin_user.check_password("adminpass123"))
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_user_string_representation(self):
        """测试用户字符串表示"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )

        expected_str = f"{user.first_name} {user.last_name} ({user.username})"
        self.assertEqual(str(user), expected_str)

    def test_user_email_unique(self):
        """测试邮箱唯一性约束"""
        User.objects.create_user(
            username="user1", email="test@example.com", password="pass123"
        )

        with self.assertRaises(Exception):
            User.objects.create_user(
                username="user2",
                email="test@example.com",  # 重复邮箱
                password="pass123",
            )


class PasswordValidationTestCase(TestCase):
    """密码验证测试"""

    def test_password_strength_validation(self):
        """测试密码强度验证"""
        # 这里可以添加自定义密码验证逻辑的测试
        pass

    def test_password_history_validation(self):
        """测试密码历史验证（如果实现了密码历史功能）"""
        pass


class PermissionTestCase(APITestCase):
    """权限控制测试"""

    def setUp(self):
        self.regular_user = User.objects.create_user(
            username="regular", email="regular@example.com", password="pass123"
        )

        self.staff_user = User.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="pass123",
            is_staff=True,
        )

        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="pass123"
        )

    def test_regular_user_permissions(self):
        """测试普通用户权限"""
        refresh = RefreshToken.for_user(self.regular_user)
        access_token = refresh.access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # 普通用户应该能访问自己的资料
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_staff_user_permissions(self):
        """测试员工用户权限"""
        refresh = RefreshToken.for_user(self.staff_user)
        access_token = refresh.access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # 员工用户应该有额外的权限
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_user_permissions(self):
        """测试管理员用户权限"""
        refresh = RefreshToken.for_user(self.admin_user)
        access_token = refresh.access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # 管理员应该有所有权限
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
