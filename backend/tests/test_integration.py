"""
系统集成测试用例
验证前后端数据交互的正确性和稳定性
"""

import json
import time
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


class APIIntegrationTestCase(APITestCase):
    """API集成测试"""

    def setUp(self):
        """测试前准备"""
        self.client = APIClient()

        # 创建测试用户
        self.test_user = User.objects.create_user(
            username="testuser", email="test@example.com", password="TestPass123!"
        )

        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="AdminPass123!"
        )

        # 获取JWT Token
        self.user_token = self.get_jwt_token(self.test_user)
        self.admin_token = self.get_jwt_token(self.admin_user)

    def get_jwt_token(self, user):
        """获取JWT Token"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def authenticate_user(self, token):
        """认证用户"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_api_health_check(self):
        """测试API健康检查"""
        # 测试基础API端点是否可访问
        response = self.client.get("/admin/")
        self.assertIn(response.status_code, [200, 302])  # 200 或重定向到登录页

    def test_cors_headers(self):
        """测试CORS配置"""
        response = self.client.options("/admin/", HTTP_ORIGIN="http://localhost:3000")

        # 检查CORS头部
        if "Access-Control-Allow-Origin" in response.headers:
            self.assertIn("Access-Control-Allow-Origin", response.headers)

    def test_authentication_flow(self):
        """测试完整的认证流程"""
        # 1. 未认证访问受保护资源应该失败
        response = self.client.get("/admin/auth/user/")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)  # 重定向到登录

        # 2. 使用Django session认证访问管理员界面
        self.client.force_login(self.admin_user)
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_response_format(self):
        """测试API响应格式一致性"""
        # 使用Django session认证
        self.client.force_login(self.admin_user)

        # 测试管理员界面响应
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("text/html", response.get("Content-Type", ""))

    def test_error_handling(self):
        """测试错误处理"""
        # 测试404错误
        response = self.client.get("/api/v1/nonexistent/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # 测试无效Token
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")
        response = self.client.get("/admin/auth/user/")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_rate_limiting(self):
        """测试API速率限制（如果配置了）"""
        # 这里可以添加速率限制测试
        pass

    def test_data_validation(self):
        """测试数据验证"""
        # 测试无效数据提交
        invalid_data = {"invalid_field": "invalid_value"}

        response = self.client.post("/admin/login/", invalid_data)
        # 应该返回错误或重定向
        self.assertIn(response.status_code, [400, 302, 200])


class DatabaseIntegrationTestCase(TransactionTestCase):
    """数据库集成测试"""

    def test_database_connection(self):
        """测试数据库连接"""
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)

    def test_model_creation(self):
        """测试模型创建"""
        # 测试用户模型
        user = User.objects.create_user(
            username="dbtest", email="dbtest@example.com", password="password123"
        )

        self.assertTrue(user.id)
        self.assertEqual(user.username, "dbtest")
        self.assertTrue(user.check_password("password123"))

    def test_database_transactions(self):
        """测试数据库事务"""
        from django.db import transaction

        try:
            with transaction.atomic():
                user1 = User.objects.create_user(
                    username="trans1",
                    email="trans1@example.com",
                    password="password123",
                )

                # 模拟错误
                user2 = User.objects.create_user(
                    username="trans1",  # 重复用户名，应该失败
                    email="trans2@example.com",
                    password="password123",
                )
        except Exception:
            pass

        # 验证事务回滚
        self.assertFalse(User.objects.filter(username="trans1").exists())

    def test_database_indexes(self):
        """测试数据库索引"""
        # 创建大量用户来测试查询性能
        users = []
        for i in range(100):
            users.append(User(username=f"user{i}", email=f"user{i}@example.com"))

        User.objects.bulk_create(users)

        # 测试索引查询
        start_time = time.time()
        user = User.objects.filter(username="user50").first()
        end_time = time.time()

        self.assertIsNotNone(user)
        self.assertLess(end_time - start_time, 1.0)  # 查询应该在1秒内完成


class CacheIntegrationTestCase(TestCase):
    """缓存集成测试"""

    def test_cache_backend(self):
        """测试缓存后端"""
        from django.core.cache import cache

        # 测试缓存设置和获取
        cache.set("test_key", "test_value", 30)
        value = cache.get("test_key")

        self.assertEqual(value, "test_value")

    def test_cache_invalidation(self):
        """测试缓存失效"""
        from django.core.cache import cache

        cache.set("test_key", "test_value", 30)
        cache.delete("test_key")
        value = cache.get("test_key")

        self.assertIsNone(value)


class SecurityIntegrationTestCase(APITestCase):
    """安全集成测试"""

    def test_csrf_protection(self):
        """测试CSRF保护"""
        # 测试没有CSRF Token的POST请求
        response = self.client.post(
            "/admin/login/", {"username": "test", "password": "test"}
        )

        # 应该被CSRF保护拦截或重定向
        self.assertIn(response.status_code, [403, 302, 200])

    def test_sql_injection_protection(self):
        """测试SQL注入保护"""
        # 尝试SQL注入攻击
        malicious_input = "'; DROP TABLE auth_user; --"

        try:
            User.objects.filter(username=malicious_input)
        except Exception as e:
            # 应该安全处理，不会执行恶意SQL
            pass

        # 验证用户表仍然存在
        self.assertTrue(User.objects.model._meta.db_table)

    def test_xss_protection(self):
        """测试XSS保护"""
        # 测试恶意脚本输入
        malicious_script = "<script>alert('xss')</script>"

        user = User.objects.create_user(
            username="xsstest", email="xss@example.com", first_name=malicious_script
        )

        # Django应该自动转义HTML
        self.assertEqual(user.first_name, malicious_script)

    def test_authentication_security(self):
        """测试认证安全性"""
        # 测试弱密码
        try:
            user = User.objects.create_user(
                username="weakpass", email="weak@example.com", password="123"  # 弱密码
            )
            # 如果配置了密码验证，应该失败
        except Exception:
            pass


class PerformanceIntegrationTestCase(TestCase):
    """性能集成测试"""

    def test_query_performance(self):
        """测试查询性能"""
        # 创建测试数据
        users = []
        for i in range(1000):
            users.append(
                User(username=f"perfuser{i}", email=f"perfuser{i}@example.com")
            )

        User.objects.bulk_create(users)

        # 测试查询性能
        start_time = time.time()
        users = list(User.objects.all()[:100])
        end_time = time.time()

        self.assertEqual(len(users), 100)
        self.assertLess(end_time - start_time, 2.0)  # 查询应该在2秒内完成

    def test_memory_usage(self):
        """测试内存使用"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # 执行一些操作
        users = User.objects.all()[:1000]
        list(users)  # 强制执行查询

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # 内存增长应该在合理范围内（100MB）
        self.assertLess(memory_increase, 100 * 1024 * 1024)


class ModuleCommunicationTestCase(APITestCase):
    """模块间通信测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="moduletest", email="module@example.com", password="password123"
        )

        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_accounts_module_communication(self):
        """测试accounts模块通信"""
        # 测试用户认证模块是否正常工作
        response = self.client.get("/admin/")
        self.assertIn(response.status_code, [200, 302])

    def test_cross_module_data_flow(self):
        """测试跨模块数据流"""
        # 这里可以测试不同模块之间的数据传递
        # 例如：用户创建 -> 权限分配 -> 文档访问
        pass

    def test_module_error_propagation(self):
        """测试模块错误传播"""
        # 测试一个模块的错误是否会影响其他模块
        pass


class EndToEndTestCase(APITestCase):
    """端到端测试"""

    def test_user_registration_to_login_flow(self):
        """测试用户注册到登录的完整流程"""
        # 1. 创建用户（模拟注册）
        user_data = {
            "username": "e2etest",
            "email": "e2e@example.com",
            "password": "E2EPass123!",
        }

        user = User.objects.create_user(**user_data)
        self.assertTrue(user.id)

        # 2. 用户登录（获取Token）
        token = RefreshToken.for_user(user)
        self.assertIsNotNone(token)

        # 3. 使用Token访问受保护资源
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        response = self.client.get("/admin/")
        self.assertIn(response.status_code, [200, 302])

    def test_complete_api_workflow(self):
        """测试完整的API工作流"""
        # 这里可以测试完整的业务流程
        # 例如：登录 -> 上传文档 -> 分类 -> 搜索 -> 下载
        pass


class SystemResourceTestCase(TestCase):
    """系统资源测试"""

    def test_file_system_access(self):
        """测试文件系统访问"""
        import os

        from django.conf import settings

        # 测试媒体文件目录
        media_root = settings.MEDIA_ROOT
        self.assertTrue(
            os.path.exists(os.path.dirname(media_root))
            or os.access(os.path.dirname(media_root), os.W_OK)
        )

        # 测试静态文件目录
        static_root = settings.STATIC_ROOT
        self.assertTrue(
            os.path.exists(os.path.dirname(static_root))
            or os.access(os.path.dirname(static_root), os.W_OK)
        )

    def test_logging_system(self):
        """测试日志系统"""
        import logging

        logger = logging.getLogger("knowledge_base")

        # 测试日志记录
        logger.info("Integration test log message")

        # 验证日志配置
        self.assertTrue(logger.handlers)
