"""
安全增强配置
"""

from .settings_dev_new import *

# API限流配置
REST_FRAMEWORK.update(
    {
        "DEFAULT_THROTTLE_CLASSES": [
            "utils.throttling.APICallThrottle",
            "utils.throttling.FileUploadThrottle",
            "utils.throttling.LoginThrottle",
        ],
        "DEFAULT_THROTTLE_RATES": {
            "anon": "50/hour",
            "user": "200/hour",
            "staff": "1000/hour",
            "upload": "10/hour",
            "login": "5/hour",
        },
    }
)

# Redis配置 (用于限流)
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# 文件上传安全配置
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644

# 安全中间件
MIDDLEWARE.insert(0, "utils.middleware.SecurityMiddleware")
MIDDLEWARE.insert(1, "utils.middleware.ThrottleMiddleware")

# CORS安全配置
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# 安全头配置
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# 日志配置
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "logs/security.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "security": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": True,
        },
        "throttling": {
            "handlers": ["file", "console"],
            "level": "WARNING",
            "propagate": True,
        },
    },
}
