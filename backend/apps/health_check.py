"""
健康检查模块
"""

import json
import time
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)


class HealthCheckService:
    """健康检查服务"""
    
    def __init__(self):
        self.checks = {
            'database': self.check_database,
            'cache': self.check_cache,
            'celery': self.check_celery,
            'elasticsearch': self.check_elasticsearch,
            'disk_space': self.check_disk_space,
            'memory': self.check_memory,
        }
    
    def check_database(self):
        """检查数据库连接"""
        try:
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'message': '数据库连接正常'
            }
        except Exception as e:
            logger.error(f"数据库健康检查失败: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': '数据库连接失败'
            }
    
    def check_cache(self):
        """检查缓存服务"""
        try:
            start_time = time.time()
            test_key = 'health_check_test'
            test_value = 'test_value'
            
            # 设置测试值
            cache.set(test_key, test_value, 60)
            
            # 获取测试值
            cached_value = cache.get(test_key)
            
            if cached_value != test_value:
                raise Exception("缓存值不匹配")
            
            # 删除测试值
            cache.delete(test_key)
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'message': '缓存服务正常'
            }
        except Exception as e:
            logger.error(f"缓存健康检查失败: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': '缓存服务异常'
            }
    
    def check_celery(self):
        """检查Celery服务"""
        try:
            from celery import current_app
            
            # 检查Celery是否可用
            inspect = current_app.control.inspect()
            
            # 获取活跃的worker
            active_workers = inspect.active()
            
            if not active_workers:
                return {
                    'status': 'warning',
                    'message': '没有活跃的Celery worker',
                    'workers': 0
                }
            
            worker_count = len(active_workers)
            
            return {
                'status': 'healthy',
                'message': f'Celery服务正常，{worker_count}个worker运行中',
                'workers': worker_count,
                'active_workers': list(active_workers.keys())
            }
            
        except ImportError:
            return {
                'status': 'warning',
                'message': 'Celery未配置'
            }
        except Exception as e:
            logger.error(f"Celery健康检查失败: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Celery服务异常'
            }
    
    def check_elasticsearch(self):
        """检查Elasticsearch服务"""
        try:
            # 这里需要根据实际的Elasticsearch配置进行调整
            import requests
            
            es_host = getattr(settings, 'ELASTICSEARCH_HOST', 'localhost:9200')
            url = f"http://{es_host}/_cluster/health"
            
            start_time = time.time()
            response = requests.get(url, timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                health_data = response.json()
                status = health_data.get('status', 'unknown')
                
                return {
                    'status': 'healthy' if status in ['green', 'yellow'] else 'unhealthy',
                    'response_time_ms': round(response_time, 2),
                    'cluster_status': status,
                    'message': f'Elasticsearch集群状态: {status}'
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': f'Elasticsearch响应异常: {response.status_code}'
                }
                
        except ImportError:
            return {
                'status': 'warning',
                'message': 'requests库未安装，无法检查Elasticsearch'
            }
        except Exception as e:
            logger.error(f"Elasticsearch健康检查失败: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Elasticsearch服务异常'
            }
    
    def check_disk_space(self):
        """检查磁盘空间"""
        try:
            import shutil
            
            # 检查应用目录的磁盘空间
            total, used, free = shutil.disk_usage('.')
            
            # 转换为GB
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)
            
            usage_percent = (used / total) * 100
            
            # 磁盘使用率超过90%为不健康
            status = 'healthy' if usage_percent < 90 else 'unhealthy'
            if usage_percent > 80:
                status = 'warning'
            
            return {
                'status': status,
                'total_gb': round(total_gb, 2),
                'used_gb': round(used_gb, 2),
                'free_gb': round(free_gb, 2),
                'usage_percent': round(usage_percent, 2),
                'message': f'磁盘使用率: {usage_percent:.1f}%'
            }
            
        except Exception as e:
            logger.error(f"磁盘空间检查失败: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': '磁盘空间检查失败'
            }
    
    def check_memory(self):
        """检查内存使用情况"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            
            # 内存使用率超过90%为不健康
            status = 'healthy' if memory.percent < 90 else 'unhealthy'
            if memory.percent > 80:
                status = 'warning'
            
            return {
                'status': status,
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'usage_percent': memory.percent,
                'message': f'内存使用率: {memory.percent:.1f}%'
            }
            
        except ImportError:
            return {
                'status': 'warning',
                'message': 'psutil库未安装，无法检查内存'
            }
        except Exception as e:
            logger.error(f"内存检查失败: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': '内存检查失败'
            }
    
    def run_all_checks(self):
        """运行所有健康检查"""
        results = {}
        overall_status = 'healthy'
        
        for check_name, check_func in self.checks.items():
            try:
                result = check_func()
                results[check_name] = result
                
                # 更新整体状态
                if result['status'] == 'unhealthy':
                    overall_status = 'unhealthy'
                elif result['status'] == 'warning' and overall_status == 'healthy':
                    overall_status = 'warning'
                    
            except Exception as e:
                logger.error(f"健康检查 {check_name} 执行失败: {str(e)}")
                results[check_name] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'message': f'{check_name} 检查执行失败'
                }
                overall_status = 'unhealthy'
        
        return {
            'overall_status': overall_status,
            'timestamp': time.time(),
            'checks': results
        }


# 健康检查视图
@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """健康检查端点"""
    health_service = HealthCheckService()
    
    # 检查是否只需要简单的存活检查
    if request.GET.get('simple') == 'true':
        return JsonResponse({
            'status': 'healthy',
            'timestamp': time.time(),
            'message': '服务运行中'
        })
    
    # 运行完整的健康检查
    results = health_service.run_all_checks()
    
    # 根据整体状态设置HTTP状态码
    status_code = 200
    if results['overall_status'] == 'unhealthy':
        status_code = 503  # Service Unavailable
    elif results['overall_status'] == 'warning':
        status_code = 200  # OK but with warnings
    
    return JsonResponse(results, status=status_code)


@csrf_exempt
@require_http_methods(["GET"])
def readiness_check(request):
    """就绪检查端点（用于Kubernetes）"""
    health_service = HealthCheckService()
    
    # 只检查关键服务
    critical_checks = ['database', 'cache']
    results = {}
    
    for check_name in critical_checks:
        if check_name in health_service.checks:
            results[check_name] = health_service.checks[check_name]()
    
    # 检查是否所有关键服务都健康
    all_healthy = all(
        result['status'] == 'healthy' 
        for result in results.values()
    )
    
    status_code = 200 if all_healthy else 503
    
    return JsonResponse({
        'ready': all_healthy,
        'timestamp': time.time(),
        'checks': results
    }, status=status_code)


@csrf_exempt
@require_http_methods(["GET"])
def liveness_check(request):
    """存活检查端点（用于Kubernetes）"""
    # 简单的存活检查，只要应用能响应就认为是存活的
    return JsonResponse({
        'alive': True,
        'timestamp': time.time(),
        'message': '应用存活'
    })


# 系统信息端点
@csrf_exempt
@require_http_methods(["GET"])
def system_info(request):
    """系统信息端点"""
    try:
        import platform
        import sys
        from django import get_version
        
        info = {
            'application': {
                'name': 'Knowledge Base System',
                'version': '1.0.0',
                'django_version': get_version(),
                'python_version': sys.version,
            },
            'system': {
                'platform': platform.platform(),
                'architecture': platform.architecture(),
                'processor': platform.processor(),
                'hostname': platform.node(),
            },
            'timestamp': time.time()
        }
        
        # 如果有权限，添加更多系统信息
        try:
            import psutil
            info['resources'] = {
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'disk_total_gb': round(psutil.disk_usage('.').total / (1024**3), 2),
            }
        except ImportError:
            pass
        
        return JsonResponse(info)
        
    except Exception as e:
        logger.error(f"获取系统信息失败: {str(e)}")
        return JsonResponse({
            'error': str(e),
            'message': '获取系统信息失败'
        }, status=500)


# URL配置
from django.urls import path

health_urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('health/ready/', readiness_check, name='readiness_check'),
    path('health/live/', liveness_check, name='liveness_check'),
    path('system/info/', system_info, name='system_info'),
]