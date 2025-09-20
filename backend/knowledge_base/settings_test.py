"""
测试环境配置
"""

from .settings_dev_new import *

# 测试数据库配置
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# 禁用缓存
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# 测试时禁用限流
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []

# 禁用日志
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
    },
}

# 测试文件存储
DEFAULT_FILE_STORAGE = "django.core.files.storage.InMemoryStorage"

# 禁用安全中间件
MIDDLEWARE = [m for m in MIDDLEWARE if "utils.middleware" not in m]

# 测试邮件后端
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# 密码验证器（测试时简化）
AUTH_PASSWORD_VALIDATORS = []

# 时区设置
USE_TZ = True

# 静态文件
STATIC_URL = "/static/"
STATIC_ROOT = None

# 媒体文件
MEDIA_URL = "/media/"
MEDIA_ROOT = None
