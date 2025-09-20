"""
性能测试用例
测试系统在各种负载下的性能表现
"""

import os
import threading
import time
from unittest.mock import patch

import psutil
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import connection
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


class DatabasePerformanceTestCase(TransactionTestCase):
    """数据库性能测试"""

    def test_bulk_user_creation(self):
        """测试批量用户创建性能"""
        start_time = time.time()

        # 批量创建1000个用户
        users = []
        for i in range(1000):
            users.append(
                User(
                    username=f"bulkuser{i}",
                    email=f"bulkuser{i}@example.com",
                    first_name=f"User{i}",
                    last_name="Test",
                )
            )

        User.objects.bulk_create(users, batch_size=100)

        end_time = time.time()
        creation_time = end_time - start_time

        # 批量创建应该在5秒内完成
        self.assertLess(creation_time, 5.0)

        # 验证创建成功
        self.assertEqual(
            User.objects.filter(username__startswith="bulkuser").count(), 1000
        )

        print(f"批量创建1000个用户耗时: {creation_time:.2f}秒")

    def test_query_performance_with_large_dataset(self):
        """测试大数据集查询性能"""
        # 创建大量测试数据
        users = []
        for i in range(5000):
            users.append(
                User(
                    username=f"queryuser{i}",
                    email=f"queryuser{i}@example.com",
                    first_name=f"Query{i}",
                    last_name="Test",
                )
            )

        User.objects.bulk_create(users, batch_size=500)

        # 测试各种查询性能
        queries = [
            ("简单查询", lambda: User.objects.filter(username="queryuser2500").first()),
            (
                "范围查询",
                lambda: list(
                    User.objects.filter(username__startswith="queryuser25")[:10]
                ),
            ),
            ("排序查询", lambda: list(User.objects.order_by("username")[:100])),
            (
                "聚合查询",
                lambda: User.objects.filter(username__startswith="queryuser").count(),
            ),
        ]

        for query_name, query_func in queries:
            start_time = time.time()
            result = query_func()
            end_time = time.time()
            query_time = end_time - start_time

            # 每个查询应该在1秒内完成
            self.assertLess(query_time, 1.0)
            print(f"{query_name}耗时: {query_time:.3f}秒")

    def test_concurrent_database_access(self):
        """测试并发数据库访问"""

        def create_users(thread_id, count):
            """线程函数：创建用户"""
            users = []
            for i in range(count):
                users.append(
                    User(
                        username=f"concurrent{thread_id}_{i}",
                        email=f"concurrent{thread_id}_{i}@example.com",
                    )
                )
            User.objects.bulk_create(users)

        # 创建5个线程，每个创建100个用户
        threads = []
        start_time = time.time()

        for i in range(5):
            thread = threading.Thread(target=create_users, args=(i, 100))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        end_time = time.time()
        concurrent_time = end_time - start_time

        # 并发创建应该在10秒内完成
        self.assertLess(concurrent_time, 10.0)

        # 验证所有用户都创建成功
        total_users = User.objects.filter(username__startswith="concurrent").count()
        self.assertEqual(total_users, 500)

        print(f"并发创建500个用户耗时: {concurrent_time:.2f}秒")

    def test_database_connection_pool(self):
        """测试数据库连接池性能"""

        def query_database():
            """执行数据库查询"""
            return User.objects.count()

        # 测试多次快速查询
        start_time = time.time()

        for _ in range(100):
            query_database()

        end_time = time.time()
        query_time = end_time - start_time

        # 100次查询应该在2秒内完成
        self.assertLess(query_time, 2.0)
        print(f"100次数据库查询耗时: {query_time:.2f}秒")


class CachePerformanceTestCase(TestCase):
    """缓存性能测试"""

    def test_cache_write_performance(self):
        """测试缓存写入性能"""
        start_time = time.time()

        # 写入1000个缓存项
        for i in range(1000):
            cache.set(f"perf_key_{i}", f"value_{i}", 300)

        end_time = time.time()
        write_time = end_time - start_time

        # 缓存写入应该在2秒内完成
        self.assertLess(write_time, 2.0)
        print(f"写入1000个缓存项耗时: {write_time:.2f}秒")

    def test_cache_read_performance(self):
        """测试缓存读取性能"""
        # 先写入测试数据
        for i in range(1000):
            cache.set(f"read_key_{i}", f"value_{i}", 300)

        start_time = time.time()

        # 读取1000个缓存项
        for i in range(1000):
            value = cache.get(f"read_key_{i}")
            self.assertEqual(value, f"value_{i}")

        end_time = time.time()
        read_time = end_time - start_time

        # 缓存读取应该在1秒内完成
        self.assertLess(read_time, 1.0)
        print(f"读取1000个缓存项耗时: {read_time:.2f}秒")

    def test_cache_vs_database_performance(self):
        """测试缓存与数据库性能对比"""
        # 创建测试用户
        user = User.objects.create_user(
            username="cachetest", email="cache@example.com", password="password123"
        )

        # 测试数据库查询性能
        start_time = time.time()
        for _ in range(100):
            User.objects.get(id=user.id)
        db_time = time.time() - start_time

        # 将用户数据放入缓存
        cache.set(f"user_{user.id}", user, 300)

        # 测试缓存查询性能
        start_time = time.time()
        for _ in range(100):
            cache.get(f"user_{user.id}")
        cache_time = time.time() - start_time

        # 缓存应该比数据库快
        self.assertLess(cache_time, db_time)
        print(f"数据库查询100次耗时: {db_time:.3f}秒")
        print(f"缓存查询100次耗时: {cache_time:.3f}秒")
        print(f"缓存比数据库快: {(db_time/cache_time):.1f}倍")


class APIPerformanceTestCase(APITestCase):
    """API性能测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="apitest", email="api@example.com", password="password123"
        )

        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_api_response_time(self):
        """测试API响应时间"""
        # 测试多个API端点的响应时间
        endpoints = [
            "/admin/",
            "/admin/auth/user/",
        ]

        for endpoint in endpoints:
            start_time = time.time()
            response = self.client.get(endpoint)
            end_time = time.time()
            response_time = end_time - start_time

            # API响应应该在1秒内
            self.assertLess(response_time, 1.0)
            print(f"{endpoint} 响应时间: {response_time:.3f}秒")

    def test_concurrent_api_requests(self):
        """测试并发API请求"""

        def make_request():
            """发送API请求"""
            response = self.client.get("/admin/")
            return response.status_code

        # 创建10个线程并发请求
        threads = []
        results = []
        start_time = time.time()

        def thread_worker():
            result = make_request()
            results.append(result)

        for _ in range(10):
            thread = threading.Thread(target=thread_worker)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        end_time = time.time()
        concurrent_time = end_time - start_time

        # 并发请求应该在5秒内完成
        self.assertLess(concurrent_time, 5.0)

        # 验证所有请求都成功
        self.assertEqual(len(results), 10)
        print(f"10个并发API请求耗时: {concurrent_time:.2f}秒")

    def test_api_throughput(self):
        """测试API吞吐量"""
        request_count = 50
        start_time = time.time()

        # 连续发送50个请求
        for _ in range(request_count):
            response = self.client.get("/admin/")
            self.assertIn(response.status_code, [200, 302])

        end_time = time.time()
        total_time = end_time - start_time
        throughput = request_count / total_time

        # 吞吐量应该至少每秒10个请求
        self.assertGreater(throughput, 10)
        print(f"API吞吐量: {throughput:.1f} 请求/秒")


class MemoryPerformanceTestCase(TestCase):
    """内存性能测试"""

    def test_memory_usage_during_bulk_operations(self):
        """测试批量操作时的内存使用"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 执行批量操作
        users = []
        for i in range(10000):
            users.append(
                User(
                    username=f"memuser{i}",
                    email=f"memuser{i}@example.com",
                    first_name=f"Memory{i}",
                    last_name="Test",
                )
            )

        User.objects.bulk_create(users, batch_size=1000)

        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory

        # 内存增长应该在合理范围内（200MB）
        self.assertLess(memory_increase, 200)
        print(f"批量创建10000个用户，内存增长: {memory_increase:.1f}MB")

        # 清理数据
        User.objects.filter(username__startswith="memuser").delete()

        # 检查内存是否释放
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_released = peak_memory - final_memory

        print(f"删除数据后，内存释放: {memory_released:.1f}MB")

    def test_query_memory_efficiency(self):
        """测试查询内存效率"""
        # 创建测试数据
        users = []
        for i in range(5000):
            users.append(
                User(username=f"queryuser{i}", email=f"queryuser{i}@example.com")
            )
        User.objects.bulk_create(users, batch_size=1000)

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024

        # 测试不同的查询方式
        # 1. 一次性加载所有数据（内存密集）
        start_time = time.time()
        all_users = list(User.objects.filter(username__startswith="queryuser"))
        load_all_time = time.time() - start_time
        peak_memory_all = process.memory_info().rss / 1024 / 1024

        del all_users  # 释放内存

        # 2. 分批加载数据（内存友好）
        start_time = time.time()
        batch_size = 100
        total_processed = 0

        queryset = User.objects.filter(username__startswith="queryuser")
        for i in range(0, queryset.count(), batch_size):
            batch = list(queryset[i : i + batch_size])
            total_processed += len(batch)
            del batch  # 及时释放内存

        batch_load_time = time.time() - start_time
        peak_memory_batch = process.memory_info().rss / 1024 / 1024

        print(
            f"一次性加载: {load_all_time:.2f}秒, 内存峰值: {peak_memory_all - initial_memory:.1f}MB"
        )
        print(
            f"分批加载: {batch_load_time:.2f}秒, 内存峰值: {peak_memory_batch - initial_memory:.1f}MB"
        )

        # 分批加载应该使用更少的内存
        self.assertLess(
            peak_memory_batch - initial_memory, peak_memory_all - initial_memory
        )


class LoadTestCase(TestCase):
    """负载测试"""

    def test_system_under_load(self):
        """测试系统负载能力"""

        # 模拟高负载情况
        def simulate_user_activity():
            """模拟用户活动"""
            # 创建用户
            user = User.objects.create_user(
                username=f"load_{threading.current_thread().ident}",
                email=f"load_{threading.current_thread().ident}@example.com",
                password="password123",
            )

            # 执行一些操作
            User.objects.filter(id=user.id).update(last_login=time.time())
            User.objects.get(id=user.id)

            return user.id

        # 创建多个线程模拟并发用户
        threads = []
        results = []
        start_time = time.time()

        def worker():
            try:
                result = simulate_user_activity()
                results.append(result)
            except Exception as e:
                results.append(f"Error: {e}")

        # 创建20个并发线程
        for _ in range(20):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        end_time = time.time()
        load_test_time = end_time - start_time

        # 负载测试应该在30秒内完成
        self.assertLess(load_test_time, 30.0)

        # 检查成功率
        successful_results = [r for r in results if isinstance(r, int)]
        success_rate = len(successful_results) / len(results) * 100

        # 成功率应该至少90%
        self.assertGreater(success_rate, 90)

        print(f"负载测试完成时间: {load_test_time:.2f}秒")
        print(f"成功率: {success_rate:.1f}%")
        print(f"处理的请求数: {len(results)}")


class ScalabilityTestCase(TestCase):
    """可扩展性测试"""

    def test_database_scalability(self):
        """测试数据库可扩展性"""
        # 测试不同数据量下的性能
        data_sizes = [100, 500, 1000, 2000]
        performance_results = []

        for size in data_sizes:
            # 创建测试数据
            users = []
            for i in range(size):
                users.append(
                    User(
                        username=f"scale{size}_{i}",
                        email=f"scale{size}_{i}@example.com",
                    )
                )

            start_time = time.time()
            User.objects.bulk_create(users, batch_size=100)
            creation_time = time.time() - start_time

            # 测试查询性能
            start_time = time.time()
            count = User.objects.filter(username__startswith=f"scale{size}_").count()
            query_time = time.time() - start_time

            performance_results.append(
                {"size": size, "creation_time": creation_time, "query_time": query_time}
            )

            self.assertEqual(count, size)

            print(
                f"数据量 {size}: 创建耗时 {creation_time:.3f}秒, 查询耗时 {query_time:.3f}秒"
            )

        # 分析性能趋势
        # 理想情况下，性能应该线性增长或接近线性
        for i in range(1, len(performance_results)):
            prev = performance_results[i - 1]
            curr = performance_results[i]

            size_ratio = curr["size"] / prev["size"]
            time_ratio = curr["creation_time"] / prev["creation_time"]

            # 时间增长不应该超过数据量增长的2倍
            self.assertLess(time_ratio, size_ratio * 2)
