"""
增强的文档管理视图
"""

import os
import time
import logging
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Document, Category, Tag
from .serializers import DocumentSerializer, DocumentDetailSerializer
from apps.ocr.services import DocumentOCRProcessor

logger = logging.getLogger(__name__)


class DocumentViewSetEnhanced(viewsets.ModelViewSet):
    """增强的文档管理视图集"""
    
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        """获取查询集"""
        queryset = Document.objects.select_related(
            'uploaded_by', 'category'
        ).prefetch_related('tags')
        
        # 权限过滤
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                models.Q(uploaded_by=self.request.user) |
                models.Q(is_public=True) |
                models.Q(shared_with=self.request.user)
            )
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """根据动作选择序列化器"""
        if self.action == 'retrieve':
            return DocumentDetailSerializer
        return DocumentSerializer
    
    def perform_create(self, serializer):
        """创建文档时的额外处理"""
        # 设置上传用户
        serializer.save(uploaded_by=self.request.user)
        
        # 异步处理OCR（如果是图片或PDF）
        document = serializer.instance
        if document.file_type in ['jpg', 'jpeg', 'png', 'pdf']:
            try:
                processor = DocumentOCRProcessor()
                processor.process_document(document)
            except Exception as e:
                logger.error(f"OCR处理失败: {e}")
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """下载文档"""
        document = self.get_object()
        
        # 检查权限
        if not self._check_access_permission(document, request.user):
            return Response(
                {'error': '无权限下载此文档'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # 增加下载计数
            document.download_count += 1
            document.save(update_fields=['download_count'])
            
            # 返回文件
            if document.file and default_storage.exists(document.file.name):
                response = HttpResponse(
                    document.file.read(),
                    content_type='application/octet-stream'
                )
                response['Content-Disposition'] = f'attachment; filename="{document.title}"'
                return response
            else:
                return Response(
                    {'error': '文件不存在'},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            logger.error(f"文档下载失败: {e}")
            return Response(
                {'error': '下载失败'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """预览文档"""
        document = self.get_object()
        
        # 检查权限
        if not self._check_access_permission(document, request.user):
            return Response(
                {'error': '无权限预览此文档'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # 增加查看计数
            document.view_count += 1
            document.save(update_fields=['view_count'])
            
            # 根据文件类型返回预览内容
            preview_data = self._generate_preview(document)
            
            return Response({
                'document_id': document.id,
                'title': document.title,
                'file_type': document.file_type,
                'preview_data': preview_data,
                'ocr_text': document.ocr_text,
                'page_count': document.page_count
            })
            
        except Exception as e:
            logger.error(f"文档预览失败: {e}")
            return Response(
                {'error': '预览失败'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def ocr_process(self, request, pk=None):
        """触发OCR处理"""
        document = self.get_object()
        
        # 检查权限
        if document.uploaded_by != request.user and not request.user.is_staff:
            return Response(
                {'error': '无权限处理此文档'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            provider = request.data.get('provider', 'tesseract')
            
            # 创建OCR处理器
            processor = DocumentOCRProcessor()
            task = processor.process_document(document, provider)
            
            if task:
                return Response({
                    'message': 'OCR处理已开始',
                    'task_id': task.id,
                    'status': task.status
                })
            else:
                return Response(
                    {'error': 'OCR处理启动失败'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"OCR处理请求失败: {e}")
            return Response(
                {'error': '处理请求失败'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """文档搜索"""
        query = request.query_params.get('q', '').strip()
        category_id = request.query_params.get('category')
        tags = request.query_params.getlist('tags')
        
        if not query:
            return Response(
                {'error': '请输入搜索关键词'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 构建搜索查询
        queryset = self.get_queryset()
        
        # 文本搜索
        from django.db.models import Q
        search_query = Q(title__icontains=query) | Q(description__icontains=query)
        if query:
            search_query |= Q(ocr_text__icontains=query)
        
        queryset = queryset.filter(search_query)
        
        # 分类过滤
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # 标签过滤
        if tags:
            queryset = queryset.filter(tags__name__in=tags).distinct()
        
        # 分页
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        total = queryset.count()
        documents = queryset[start:end]
        
        serializer = self.get_serializer(documents, many=True)
        
        return Response({
            'results': serializer.data,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        })
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """获取分类列表"""
        categories = Category.objects.all().order_by('name')
        data = [
            {
                'id': cat.id,
                'name': cat.name,
                'description': cat.description,
                'color': cat.color,
                'document_count': cat.documents.count()
            }
            for cat in categories
        ]
        return Response({'categories': data})
    
    @action(detail=False, methods=['get'])
    def tags(self, request):
        """获取标签列表"""
        tags = Tag.objects.all().order_by('name')
        data = [
            {
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'document_count': tag.documents.count()
            }
            for tag in tags
        ]
        return Response({'tags': data})
    
    def _check_access_permission(self, document, user):
        """检查访问权限"""
        if user.is_staff:
            return True
        if document.uploaded_by == user:
            return True
        if document.is_public:
            return True
        if document.shared_with.filter(id=user.id).exists():
            return True
        return False
    
    def _generate_preview(self, document):
        """生成文档预览"""
        try:
            if document.file_type in ['txt']:
                # 文本文件直接读取内容
                content = document.file.read().decode('utf-8')
                return {
                    'type': 'text',
                    'content': content[:5000]  # 限制预览长度
                }
            
            elif document.file_type in ['jpg', 'jpeg', 'png']:
                # 图片文件返回URL
                return {
                    'type': 'image',
                    'url': document.file.url if document.file else None,
                    'ocr_text': document.ocr_text
                }
            
            elif document.file_type == 'pdf':
                # PDF文件返回基本信息和OCR文本
                return {
                    'type': 'pdf',
                    'page_count': document.page_count,
                    'ocr_text': document.ocr_text,
                    'thumbnail': document.thumbnail.url if document.thumbnail else None
                }
            
            else:
                # 其他文件类型返回基本信息
                return {
                    'type': 'file',
                    'file_type': document.file_type,
                    'file_size': document.file_size,
                    'description': document.description
                }
                
        except Exception as e:
            logger.error(f"生成预览失败: {e}")
            return {
                'type': 'error',
                'message': '预览生成失败'
            }