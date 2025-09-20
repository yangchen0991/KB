"""
简单的监控视图 - 用于健康检查
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import connection
import psutil
import os

@csrf_exempt
@require_http_methods(["GET"])
def simple_health_check(request):
    """简单的健康检查 - 不需要认证"""
    try:
        # 检查数据库连接
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"
            
        # 获取数据库表数量
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            table_count = cursor.fetchone()[0] if cursor.fetchone() else 0
            
    except Exception as e:
        db_status = "unhealthy"
        table_count = 0
    
    try:
        # 获取系统资源信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        resources = {
            "cpu_percent": round(cpu_percent, 1),
            "memory_percent": round(memory.percent, 1),
            "disk_percent": round(disk.percent, 1)
        }
    except Exception:
        resources = {
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_percent": 0
        }
    
    # 构建响应数据
    health_data = {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": timezone.now().isoformat(),
        "database": {
            "status": db_status,
            "tables": table_count
        },
        "server": {
            "status": "healthy",
            "status_code": 200
        },
        "resources": resources,
        "services": {
            "database": {
                "status": "healthy" if db_status == "healthy" else "unhealthy",
                "message": "数据库连接正常" if db_status == "healthy" else "数据库连接失败"
            },
            "server": {
                "status": "healthy",
                "message": "服务器运行正常"
            }
        }
    }
    
    return JsonResponse(health_data)