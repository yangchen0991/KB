from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

def home_view(request):
    """后端API服务欢迎页面"""
    context = {
        'title': '知识库系统 API 服务',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': [
            {'path': '/admin/', 'description': 'Django管理后台'},
            {'path': '/api/v1/auth/', 'description': '用户认证API'},
            {'path': '/api/v1/documents/', 'description': '文档管理API'},
            {'path': '/api/v1/search/', 'description': '搜索API'},
            {'path': '/api/v1/monitoring/', 'description': '监控API'},
        ]
    }
    return render(request, 'core/home.html', context)

def api_status(request):
    """API状态检查"""
    return JsonResponse({
        'status': 'ok',
        'message': '知识库系统API服务正常运行',
        'version': '1.0.0',
        'timestamp': '2025-09-21T00:18:00Z'
    })