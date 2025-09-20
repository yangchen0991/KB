"""
监控中间件
自动收集HTTP请求指标和性能数据
"""

import logging
import time

from django.core.cache import cache
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

from .prometheus_client import prometheus_client

logger = logging.getLogger(__name__)


class PrometheusMiddleware(MiddlewareMixin):
    """Prometheus指标收集中间件"""

    def process_request(self, request):
        """请求开始时记录时间"""
        request._prometheus_start_time = time.time()
        return None

    def process_response(self, request, response):
        """请求结束时记录指标"""
        try:
            # 计算请求时长
            start_time = getattr(request, "_prometheus_start_time", None)
            if start_time:
                duration = time.time() - start_time

                # 获取请求信息
                method = request.method
                path = request.path
                status_code = response.status_code

                # 简化路径（移除ID等动态部分）
                endpoint = self._normalize_path(path)

                # 记录HTTP请求指标
                prometheus_client.record_http_request(
                    method=method,
                    endpoint=endpoint,
                    status_code=status_code,
                    duration=duration,
                )

                # 更新缓存中的统计信息
                self._update_request_stats(method, endpoint, status_code, duration)

        except Exception as e:
            logger.error(f"Prometheus中间件错误: {str(e)}")

        return response

    def process_exception(self, request, exception):
        """处理异常时记录错误指标"""
        try:
            # 记录错误
            method = request.method
            path = request.path
            endpoint = self._normalize_path(path)

            prometheus_client.record_http_request(
                method=method, endpoint=endpoint, status_code=500, duration=0
            )

            # 更新错误统计
            self._update_error_stats()

        except Exception as e:
            logger.error(f"Prometheus异常处理错误: {str(e)}")

        return None

    def _normalize_path(self, path: str) -> str:
        """标准化路径，移除动态部分"""
        # 移除UUID和数字ID
        import re

        # 替换UUID
        path = re.sub(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/",
            "/{id}/",
            path,
        )

        # 替换数字ID
        path = re.sub(r"/\d+/", "/{id}/", path)

        # 移除查询参数
        if "?" in path:
            path = path.split("?")[0]

        return path

    def _update_request_stats(
        self, method: str, endpoint: str, status_code: int, duration: float
    ):
        """更新请求统计信息"""
        try:
            # 更新总请求数
            cache_key = "total_requests_today"
            current_count = cache.get(cache_key, 0)
            cache.set(cache_key, current_count + 1, 86400)  # 24小时过期

            # 更新错误率
            if status_code >= 400:
                error_key = "error_requests_today"
                error_count = cache.get(error_key, 0)
                cache.set(error_key, error_count + 1, 86400)

                # 计算错误率
                total_requests = cache.get(cache_key, 1)
                error_rate = (error_count / total_requests) * 100
                cache.set("error_rate", error_rate, 86400)

            # 更新平均响应时间
            avg_key = "avg_response_time"
            current_avg = cache.get(avg_key, 0)
            request_count = cache.get("response_time_count", 0)

            new_avg = ((current_avg * request_count) + duration) / (request_count + 1)
            cache.set(avg_key, new_avg, 86400)
            cache.set("response_time_count", request_count + 1, 86400)

        except Exception as e:
            logger.error(f"更新请求统计失败: {str(e)}")

    def _update_error_stats(self):
        """更新错误统计"""
        try:
            # 更新严重错误数
            critical_key = "critical_errors_today"
            current_count = cache.get(critical_key, 0)
            cache.set(critical_key, current_count + 1, 86400)

        except Exception as e:
            logger.error(f"更新错误统计失败: {str(e)}")


class ActiveUsersMiddleware(MiddlewareMixin):
    """活跃用户统计中间件"""

    def process_request(self, request):
        """记录活跃用户"""
        try:
            if request.user.is_authenticated:
                # 使用Redis Set记录活跃用户
                cache_key = "active_users_set"
                user_id = str(request.user.id)

                # 获取当前活跃用户集合
                active_users = cache.get(cache_key, set())
                if not isinstance(active_users, set):
                    active_users = set()

                # 添加当前用户
                active_users.add(user_id)

                # 更新缓存（15分钟过期）
                cache.set(cache_key, active_users, 900)

                # 更新活跃用户数量
                cache.set("active_users_count", len(active_users), 900)

        except Exception as e:
            logger.error(f"活跃用户中间件错误: {str(e)}")

        return None


class SearchMetricsMiddleware(MiddlewareMixin):
    """搜索指标中间件"""

    def process_request(self, request):
        """检查是否为搜索请求"""
        if "/api/search/" in request.path:
            request._is_search_request = True
            request._search_start_time = time.time()
        return None

    def process_response(self, request, response):
        """记录搜索指标"""
        try:
            if getattr(request, "_is_search_request", False):
                start_time = getattr(request, "_search_start_time", None)
                if start_time:
                    duration = (time.time() - start_time) * 1000  # 转换为毫秒
                    success = response.status_code == 200

                    # 记录Prometheus指标
                    prometheus_client.record_search_request(duration / 1000, success)

                    # 更新缓存统计
                    self._update_search_stats(duration, success)

        except Exception as e:
            logger.error(f"搜索指标中间件错误: {str(e)}")

        return response

    def _update_search_stats(self, duration: float, success: bool):
        """更新搜索统计"""
        try:
            # 更新搜索请求数
            search_key = "search_requests_today"
            current_count = cache.get(search_key, 0)
            cache.set(search_key, current_count + 1, 86400)

            # 更新平均响应时间
            avg_key = "avg_search_response_time"
            current_avg = cache.get(avg_key, 0)
            count_key = "search_response_time_count"
            request_count = cache.get(count_key, 0)

            new_avg = ((current_avg * request_count) + duration) / (request_count + 1)
            cache.set(avg_key, new_avg, 86400)
            cache.set(count_key, request_count + 1, 86400)

            # 更新成功率
            if success:
                success_key = "search_success_today"
                success_count = cache.get(success_key, 0)
                cache.set(success_key, success_count + 1, 86400)

            total_searches = cache.get(search_key, 1)
            successful_searches = cache.get("search_success_today", 0)
            success_rate = (successful_searches / total_searches) * 100
            cache.set("search_success_rate", success_rate, 86400)

        except Exception as e:
            logger.error(f"更新搜索统计失败: {str(e)}")
