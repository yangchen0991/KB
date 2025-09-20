"""
搜索视图
"""

import time
from django.db.models import Q, F
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.models import Document
from apps.documents.serializers import DocumentSerializer
from .models import SearchQuery, PopularSearch
from .serializers import SearchQuerySerializer, PopularSearchSerializer
from .services import SearchService


class SearchViewSet(viewsets.ViewSet):
    """搜索视图集"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def search_documents(self, request):
        """文档搜索"""
        start_time = time.time()
        
        query = request.data.get('query', '').strip()
        if not query:
            return Response(
                {'error': '请输入搜索关键词'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 搜索参数
        filters = {
            'category': request.data.get('category'),
            'tags': request.data.get('tags', []),
            'file_type': request.data.get('file_type'),
            'date_from': request.data.get('date_from'),
            'date_to': request.data.get('date_to'),
        }
        
        sort_by = request.data.get('sort_by', 'relevance')
        page = int(request.data.get('page', 1))
        page_size = int(request.data.get('page_size', 20))
        
        # 执行搜索
        search_service = SearchService()
        results = search_service.search_documents(
            query=query,
            filters=filters,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
            user=request.user
        )
        
        execution_time = time.time() - start_time
        
        # 记录搜索查询
        SearchQuery.objects.create(
            user=request.user,
            query=query,
            filters=filters,
            results_count=results['total'],
            execution_time=execution_time
        )
        
        # 更新热门搜索
        popular_search, created = PopularSearch.objects.get_or_create(
            query=query,
            defaults={'search_count': 1}
        )
        if not created:
            popular_search.search_count = F('search_count') + 1
            popular_search.save(update_fields=['search_count', 'last_searched'])
        
        # 添加执行时间到响应
        results['execution_time'] = execution_time
        
        return Response(results)
    
    @action(detail=False, methods=['get'])
    def suggestions(self, request):
        """搜索建议"""
        query = request.query_params.get('q', '').strip()
        
        if len(query) < 2:
            return Response({'suggestions': []})
        
        # 从热门搜索中获取建议
        suggestions = PopularSearch.objects.filter(
            query__icontains=query
        ).order_by('-search_count')[:10]
        
        # 从文档标题中获取建议
        document_suggestions = Document.objects.filter(
            Q(title__icontains=query) | Q(tags__name__icontains=query)
        ).values_list('title', flat=True).distinct()[:5]
        
        all_suggestions = []
        
        # 添加热门搜索建议
        for suggestion in suggestions:
            all_suggestions.append({
                'text': suggestion.query,
                'type': 'popular',
                'count': suggestion.search_count
            })
        
        # 添加文档标题建议
        for title in document_suggestions:
            all_suggestions.append({
                'text': title,
                'type': 'document',
                'count': 0
            })
        
        return Response({'suggestions': all_suggestions[:10]})
    
    @method_decorator(cache_page(60 * 30))  # 缓存30分钟
    @action(detail=False, methods=['get'])
    def popular_searches(self, request):
        """热门搜索"""
        popular = PopularSearch.objects.all()[:20]
        serializer = PopularSearchSerializer(popular, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search_history(self, request):
        """搜索历史"""
        history = SearchQuery.objects.filter(
            user=request.user
        ).order_by('-created_at')[:50]
        
        serializer = SearchQuerySerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def advanced_search(self, request):
        """高级搜索"""
        start_time = time.time()
        
        # 高级搜索参数
        params = {
            'title': request.data.get('title', ''),
            'content': request.data.get('content', ''),
            'category': request.data.get('category'),
            'tags': request.data.get('tags', []),
            'file_type': request.data.get('file_type'),
            'uploaded_by': request.data.get('uploaded_by'),
            'date_from': request.data.get('date_from'),
            'date_to': request.data.get('date_to'),
            'file_size_min': request.data.get('file_size_min'),
            'file_size_max': request.data.get('file_size_max'),
        }
        
        sort_by = request.data.get('sort_by', 'created_at')
        page = int(request.data.get('page', 1))
        page_size = int(request.data.get('page_size', 20))
        
        # 执行高级搜索
        search_service = SearchService()
        results = search_service.advanced_search(
            params=params,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
            user=request.user
        )
        
        execution_time = time.time() - start_time
        results['execution_time'] = execution_time
        
        return Response(results)


class SearchAnalyticsView(APIView):
    """搜索分析视图"""
    
    permission_classes = [IsAuthenticated]
    
    @method_decorator(cache_page(60 * 60))  # 缓存1小时
    def get(self, request):
        """获取搜索分析数据"""
        from django.db.models import Count, Avg
        from datetime import datetime, timedelta
        
        # 时间范围
        days = int(request.query_params.get('days', 30))
        start_date = datetime.now() - timedelta(days=days)
        
        # 搜索统计
        search_stats = SearchQuery.objects.filter(
            created_at__gte=start_date
        ).aggregate(
            total_searches=Count('id'),
            avg_results=Avg('results_count'),
            avg_execution_time=Avg('execution_time')
        )
        
        # 每日搜索量
        daily_searches = SearchQuery.objects.filter(
            created_at__gte=start_date
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        # 热门查询
        popular_queries = SearchQuery.objects.filter(
            created_at__gte=start_date
        ).values('query').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # 零结果查询
        zero_result_queries = SearchQuery.objects.filter(
            created_at__gte=start_date,
            results_count=0
        ).values('query').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return Response({
            'overview': search_stats,
            'daily_searches': list(daily_searches),
            'popular_queries': list(popular_queries),
            'zero_result_queries': list(zero_result_queries)
        })