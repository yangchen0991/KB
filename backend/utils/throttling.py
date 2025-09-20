"""
API限流机制 - 令牌桶算法实现
"""

import time

import redis
from django.conf import settings
from rest_framework.exceptions import Throttled
from rest_framework.throttling import BaseThrottle


class TokenBucketThrottle(BaseThrottle):
    """令牌桶限流算法"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host=getattr(settings, "REDIS_HOST", "localhost"),
            port=getattr(settings, "REDIS_PORT", 6379),
            db=getattr(settings, "REDIS_DB", 0),
            decode_responses=True,
        )

    def allow_request(self, request, view):
        """检查请求是否被允许"""
        # 获取限流配置
        rate_config = self.get_rate_config(request, view)
        if not rate_config:
            return True

        capacity, refill_rate, window = rate_config
        key = self.get_cache_key(request, view)

        return self._check_token_bucket(key, capacity, refill_rate, window)

    def get_rate_config(self, request, view):
        """获取限流配置"""
        # 根据用户类型和端点设置不同的限流策略
        if hasattr(view, "throttle_classes"):
            # 文件上传限制更严格
            if "upload" in request.path:
                return (5, 1, 60)  # 5个令牌，每分钟补充1个
            # API调用限制
            elif request.user.is_authenticated:
                return (100, 10, 60)  # 100个令牌，每分钟补充10个
            else:
                return (20, 2, 60)  # 匿名用户：20个令牌，每分钟补充2个
        return None

    def get_cache_key(self, request, view):
        """生成缓存键"""
        if request.user.is_authenticated:
            ident = request.user.id
        else:
            ident = self.get_ident(request)

        return f"throttle:token_bucket:{ident}:{view.__class__.__name__}"

    def _check_token_bucket(self, key, capacity, refill_rate, window):
        """令牌桶算法核心逻辑"""
        now = time.time()

        # 使用Redis管道确保原子性
        pipe = self.redis_client.pipeline()

        try:
            # 获取当前桶状态
            bucket_data = self.redis_client.hmget(key, "tokens", "last_refill")

            if bucket_data[0] is None:
                # 初始化桶
                tokens = capacity
                last_refill = now
            else:
                tokens = float(bucket_data[0])
                last_refill = float(bucket_data[1])

            # 计算需要补充的令牌数
            time_passed = now - last_refill
            tokens_to_add = time_passed * (refill_rate / window)
            tokens = min(capacity, tokens + tokens_to_add)

            # 检查是否有足够的令牌
            if tokens >= 1:
                tokens -= 1

                # 更新桶状态
                pipe.hmset(key, {"tokens": tokens, "last_refill": now})
                pipe.expire(key, window * 2)  # 设置过期时间
                pipe.execute()

                return True
            else:
                # 令牌不足，更新最后检查时间
                pipe.hmset(key, {"tokens": tokens, "last_refill": now})
                pipe.expire(key, window * 2)
                pipe.execute()

                return False

        except Exception as e:
            # Redis连接失败时允许请求通过
            return True

    def wait(self):
        """返回等待时间"""
        return 60  # 建议等待60秒


class FileUploadThrottle(TokenBucketThrottle):
    """文件上传专用限流"""

    def get_rate_config(self, request, view):
        """文件上传限流配置"""
        if request.user.is_authenticated:
            return (3, 1, 300)  # 3个令牌，每5分钟补充1个
        else:
            return (1, 1, 600)  # 匿名用户：1个令牌，每10分钟补充1个


class APICallThrottle(TokenBucketThrottle):
    """API调用限流"""

    def get_rate_config(self, request, view):
        """API调用限流配置"""
        if request.user.is_authenticated:
            if request.user.is_staff:
                return (1000, 100, 60)  # 管理员：1000个令牌/分钟
            else:
                return (200, 20, 60)  # 普通用户：200个令牌/分钟
        else:
            return (50, 5, 60)  # 匿名用户：50个令牌/分钟


class LoginThrottle(TokenBucketThrottle):
    """登录限流 - 防止暴力破解"""

    def get_rate_config(self, request, view):
        """登录限流配置"""
        return (5, 1, 300)  # 5次尝试，每5分钟补充1次

    def get_cache_key(self, request, view):
        """基于IP地址的限流"""
        ident = self.get_ident(request)
        return f"throttle:login:{ident}"


# 恶意请求检测
class MaliciousRequestDetector:
    """恶意请求检测器"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host=getattr(settings, "REDIS_HOST", "localhost"),
            port=getattr(settings, "REDIS_PORT", 6379),
            db=getattr(settings, "REDIS_DB", 0),
            decode_responses=True,
        )

    def is_malicious(self, request):
        """检测是否为恶意请求"""
        ip = self.get_client_ip(request)

        # 检查黑名单
        if self.is_blacklisted(ip):
            return True

        # 检查请求频率异常
        if self.check_frequency_anomaly(ip):
            return True

        # 检查可疑User-Agent
        if self.check_suspicious_user_agent(request):
            return True

        return False

    def is_blacklisted(self, ip):
        """检查IP是否在黑名单中"""
        return self.redis_client.sismember("blacklist:ips", ip)

    def check_frequency_anomaly(self, ip):
        """检查请求频率异常"""
        key = f"frequency:{ip}"
        current_count = self.redis_client.incr(key)

        if current_count == 1:
            self.redis_client.expire(key, 60)  # 1分钟窗口

        # 如果1分钟内请求超过100次，标记为异常
        if current_count > 100:
            self.add_to_blacklist(ip, 3600)  # 加入黑名单1小时
            return True

        return False

    def check_suspicious_user_agent(self, request):
        """检查可疑User-Agent"""
        user_agent = request.META.get("HTTP_USER_AGENT", "").lower()

        suspicious_patterns = [
            "bot",
            "crawler",
            "spider",
            "scraper",
            "curl",
            "wget",
            "python-requests",
        ]

        return any(pattern in user_agent for pattern in suspicious_patterns)

    def add_to_blacklist(self, ip, duration=3600):
        """添加IP到黑名单"""
        self.redis_client.sadd("blacklist:ips", ip)
        self.redis_client.expire("blacklist:ips", duration)

    def get_client_ip(self, request):
        """获取客户端IP"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
