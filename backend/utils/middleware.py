"""
安全中间件
"""

import logging
import time

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from .throttling import MaliciousRequestDetector

logger = logging.getLogger("security")


class SecurityMiddleware(MiddlewareMixin):
    """安全中间件 - 恶意请求检测"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.detector = MaliciousRequestDetector()
        super().__init__(get_response)

    def process_request(self, request):
        """处理请求前的安全检查"""
        # 检测恶意请求
        if self.detector.is_malicious(request):
            logger.warning(
                f"恶意请求被阻止: {request.META.get('REMOTE_ADDR')} - {request.path}"
            )
            return JsonResponse(
                {"error": "请求被拒绝", "code": "MALICIOUS_REQUEST"}, status=403
            )

        # 记录请求开始时间
        request._start_time = time.time()

        return None

    def process_response(self, request, response):
        """处理响应"""
        # 记录请求处理时间
        if hasattr(request, "_start_time"):
            duration = time.time() - request._start_time
            if duration > 5.0:  # 超过5秒的请求记录警告
                logger.warning(f"慢请求: {request.path} - {duration:.2f}s")

        # 添加安全头
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


class ThrottleMiddleware(MiddlewareMixin):
    """限流中间件"""

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def process_request(self, request):
        """请求限流检查"""
        # 这里可以添加全局限流逻辑
        # 具体的限流在DRF的throttle类中实现
        return None


class RequestLoggingMiddleware(MiddlewareMixin):
    """请求日志中间件"""

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def process_request(self, request):
        """记录请求信息"""
        logger.info(
            f"请求: {request.method} {request.path} - IP: {self.get_client_ip(request)}"
        )
        return None

    def process_response(self, request, response):
        """记录响应信息"""
        logger.info(f"响应: {response.status_code} - {request.path}")
        return response

    def get_client_ip(self, request):
        """获取客户端IP"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
