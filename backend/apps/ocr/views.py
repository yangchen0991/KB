"""
OCR识别视图
"""

import logging
from django.conf import settings
from django.db import models
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.documents.models import Document
from .models import OCRTask, OCRResult
from .serializers import OCRTaskSerializer, OCRResultSerializer
from .services import DocumentOCRProcessor

logger = logging.getLogger(__name__)


class OCRViewSet(viewsets.ModelViewSet):
    """OCR识别视图集"""
    
    serializer_class = OCRTaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return OCRTask.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def process_document(self, request):
        """处理文档OCR识别"""
        document_id = request.data.get('document_id')
        provider = request.data.get('provider', 'tesseract')
        
        if not document_id:
            return Response(
                {'error': '请提供文档ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 获取文档
            document = get_object_or_404(Document, id=document_id)
            
            # 检查权限
            if document.uploaded_by != request.user and not document.is_public:
                return Response(
                    {'error': '无权限访问此文档'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # 检查是否已有处理中的任务
            existing_task = OCRTask.objects.filter(
                document=document,
                status__in=['pending', 'processing']
            ).first()
            
            if existing_task:
                return Response(
                    {'error': '文档正在处理中，请稍后再试'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 创建OCR处理器并处理文档
            processor = DocumentOCRProcessor()
            task = processor.process_document(document, provider)
            
            if task:
                serializer = self.get_serializer(task)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': 'OCR处理失败'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Document.DoesNotExist:
            return Response(
                {'error': '文档不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"OCR处理请求失败: {e}")
            return Response(
                {'error': '处理请求失败'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def result(self, request, pk=None):
        """获取OCR识别结果"""
        task = self.get_object()
        
        try:
            result = task.result
            serializer = OCRResultSerializer(result)
            return Response(serializer.data)
        except OCRResult.DoesNotExist:
            return Response(
                {'error': 'OCR结果不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def providers(self, request):
        """获取可用的OCR提供商"""
        providers = [
            {
                'key': 'tesseract',
                'name': 'Tesseract',
                'description': '开源OCR引擎，免费使用',
                'supported_languages': ['zh-cn', 'en', 'zh-tw'],
                'available': True
            },
            {
                'key': 'baidu',
                'name': '百度OCR',
                'description': '百度智能云OCR服务',
                'supported_languages': ['zh-cn', 'en'],
                'available': hasattr(settings, 'OCR_CONFIG') and 'baidu' in settings.OCR_CONFIG
            },
            {
                'key': 'tencent',
                'name': '腾讯OCR',
                'description': '腾讯云OCR服务',
                'supported_languages': ['zh-cn', 'en'],
                'available': False
            },
            {
                'key': 'aliyun',
                'name': '阿里云OCR',
                'description': '阿里云OCR服务',
                'supported_languages': ['zh-cn', 'en'],
                'available': False
            },
            {
                'key': 'azure',
                'name': 'Azure OCR',
                'description': '微软Azure认知服务OCR',
                'supported_languages': ['zh-cn', 'en'],
                'available': False
            }
        ]
        
        return Response({'providers': providers})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取OCR统计信息"""
        user_tasks = self.get_queryset()
        
        stats = {
            'total_tasks': user_tasks.count(),
            'completed_tasks': user_tasks.filter(status='completed').count(),
            'failed_tasks': user_tasks.filter(status='failed').count(),
            'processing_tasks': user_tasks.filter(status__in=['pending', 'processing']).count(),
            'total_processing_time': sum(
                task.processing_time or 0 
                for task in user_tasks.filter(processing_time__isnull=False)
            ),
            'average_confidence': user_tasks.filter(
                confidence_score__isnull=False
            ).aggregate(
                avg_confidence=models.Avg('confidence_score')
            )['avg_confidence'] or 0
        }
        
        return Response(stats)