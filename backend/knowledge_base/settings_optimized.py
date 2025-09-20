"""
Django优化设置 - 环境稳定性增强
"""

from .settings import *

# 数据库优化
DATABASES['default'].update({
    'OPTIONS': {
        'timeout': 20,
        'check_same_thread': False,
    },
    'CONN_MAX_AGE': 600,  # 连接池
})

# 缓存配置
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# 性能优化
USE_TZ = True
USE_I18N = False  # 如果不需要国际化
USE_L10N = False  # 如果不需要本地化

# 安全优化
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# 会话优化
SESSION_COOKIE_AGE = 3600  # 1小时
SESSION_SAVE_EVERY_REQUEST = False
