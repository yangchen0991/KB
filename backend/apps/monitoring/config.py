"""
监控系统配置
"""

from datetime import timedelta

# 监控收集器配置
MONITORING_COLLECTORS = {
    'system': {
        'class': 'apps.monitoring.collectors.SystemMetricsCollector',
        'interval': 30,  # 30秒
        'enabled': True,
    },
    'application': {
        'class': 'apps.monitoring.collectors.ApplicationMetricsCollector', 
        'interval': 60,  # 60秒
        'enabled': True,
    },
}

# 数据保留策略
MONITORING_RETENTION = {
    'system_metrics': timedelta(days=30),
    'application_metrics': timedelta(days=90),
    'alert_instances': timedelta(days=180),
}

# 告警阈值配置
MONITORING_THRESHOLDS = {
    'cpu_usage': 80.0,
    'memory_usage': 85.0,
    'disk_usage': 90.0,
    'error_rate': 5.0,
    'response_time': 1000.0,
}

# 性能优化配置
MONITORING_PERFORMANCE = {
    'batch_size': 100,
    'cache_timeout': 300,
    'max_connections': 10,
    'compression_enabled': True,
}
