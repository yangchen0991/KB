"""
监控数据收集器
"""

import logging
import psutil
import threading
import time
from datetime import datetime, timedelta
from django.db import transaction
from django.conf import settings
from .models import SystemMetrics, ApplicationMetrics

logger = logging.getLogger(__name__)

class BaseCollector:
    """基础收集器"""
    
    def __init__(self, interval=60):
        self.interval = interval
        self.running = False
        self.thread = None
    
    def start(self):
        """启动收集器"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            logger.info(f"{self.__class__.__name__} 已启动")
    
    def stop(self):
        """停止收集器"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info(f"{self.__class__.__name__} 已停止")
    
    def _run(self):
        """运行循环"""
        while self.running:
            try:
                self.collect()
            except Exception as e:
                logger.error(f"{self.__class__.__name__} 收集失败: {e}")
            
            time.sleep(self.interval)
    
    def collect(self):
        """收集数据 - 子类实现"""
        raise NotImplementedError

class SystemMetricsCollector(BaseCollector):
    """系统指标收集器"""
    
    def collect(self):
        """收集系统指标"""
        try:
            # CPU指标
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 负载平均值（Windows上可能不可用）
            try:
                load_avg = psutil.getloadavg()
            except AttributeError:
                load_avg = (0, 0, 0)
            
            # 内存指标
            memory = psutil.virtual_memory()
            
            # 磁盘指标
            disk = psutil.disk_usage('.')
            
            # 网络指标
            try:
                network = psutil.net_io_counters()
                network_sent = network.bytes_sent
                network_recv = network.bytes_recv
            except:
                network_sent = 0
                network_recv = 0
            
            # 创建指标记录
            with transaction.atomic():
                SystemMetrics.objects.create(
                    cpu_usage_percent=cpu_percent,
                    cpu_load_1m=load_avg[0],
                    cpu_load_5m=load_avg[1], 
                    cpu_load_15m=load_avg[2],
                    memory_usage_percent=memory.percent,
                    memory_used_bytes=memory.used,
                    memory_total_bytes=memory.total,
                    disk_usage_percent=(disk.used / disk.total) * 100,
                    disk_used_bytes=disk.used,
                    disk_total_bytes=disk.total,
                    network_bytes_sent=network_sent,
                    network_bytes_recv=network_recv,
                    active_connections=0,  # 需要实现
                    request_count=0,       # 需要实现
                    error_count=0,         # 需要实现
                )
                
            logger.debug("系统指标收集完成")
            
        except Exception as e:
            logger.error(f"系统指标收集失败: {e}")

class ApplicationMetricsCollector(BaseCollector):
    """应用指标收集器"""
    
    def collect(self):
        """收集应用指标"""
        try:
            from django.contrib.auth import get_user_model
            from apps.documents.models import Document
            
            User = get_user_model()
            
            # 用户指标
            total_users = User.objects.count()
            
            # 活跃用户（最近24小时登录）
            yesterday = datetime.now() - timedelta(days=1)
            active_users = User.objects.filter(
                last_login__gte=yesterday
            ).count()
            
            # 今日新用户
            today = datetime.now().date()
            new_users_today = User.objects.filter(
                date_joined__date=today
            ).count()
            
            # 文档指标
            total_documents = Document.objects.count()
            
            # 今日上传文档
            documents_uploaded_today = Document.objects.filter(
                created_at__date=today
            ).count()
            
            # 文档总大小
            from django.db.models import Sum
            total_size = Document.objects.aggregate(
                total=Sum('file_size')
            )['total'] or 0
            
            # 工作流指标（如果工作流应用可用）
            workflow_executions_today = 0
            workflow_success_rate = 0
            avg_workflow_duration = 0
            
            try:
                from apps.workflow.models import WorkflowExecution
                
                today_executions = WorkflowExecution.objects.filter(
                    created_at__date=today
                )
                workflow_executions_today = today_executions.count()
                
                if workflow_executions_today > 0:
                    success_count = today_executions.filter(
                        status='completed'
                    ).count()
                    workflow_success_rate = (success_count / workflow_executions_today) * 100
                    
            except ImportError:
                pass
            
            # 创建指标记录
            with transaction.atomic():
                ApplicationMetrics.objects.create(
                    active_users=active_users,
                    total_users=total_users,
                    new_users_today=new_users_today,
                    total_documents=total_documents,
                    documents_uploaded_today=documents_uploaded_today,
                    total_document_size=total_size,
                    search_requests_today=0,        # 需要实现
                    avg_search_response_time=0,     # 需要实现
                    search_success_rate=0,          # 需要实现
                    workflow_executions_today=workflow_executions_today,
                    workflow_success_rate=workflow_success_rate,
                    avg_workflow_duration=avg_workflow_duration,
                    error_rate=0,                   # 需要实现
                    critical_errors=0,              # 需要实现
                )
                
            logger.debug("应用指标收集完成")
            
        except Exception as e:
            logger.error(f"应用指标收集失败: {e}")

# 全局收集器实例
_collectors = {}

def start_collectors():
    """启动所有收集器"""
    # global _collectors  # 注释掉未使用的全局变量声明
    
    if _collectors:
        return  # 已经启动
    
    try:
        # 系统指标收集器
        system_collector = SystemMetricsCollector(interval=30)
        system_collector.start()
        _collectors['system'] = system_collector
        
        # 应用指标收集器
        app_collector = ApplicationMetricsCollector(interval=60)
        app_collector.start()
        _collectors['application'] = app_collector
        
        logger.info("所有监控收集器已启动")
        
    except Exception as e:
        logger.error(f"启动监控收集器失败: {e}")

def stop_collectors():
    """停止所有收集器"""
    # global _collectors  # 注释掉未使用的全局变量声明
    
    for name, collector in _collectors.items():
        try:
            collector.stop()
        except Exception as e:
            logger.error(f"停止收集器 {name} 失败: {e}")
    
    _collectors.clear()
    logger.info("所有监控收集器已停止")
