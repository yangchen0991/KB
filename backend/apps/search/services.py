"""
搜索服务
"""

import re
from typing import Dict, List, Optional, Any
from django.db.models import Q, Case, When, IntegerField, F
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

from apps.documents.models import Document, Category, Tag
from apps.documents.serializers import DocumentSerializer

User = get_user_model()


class SearchService:
    """搜索服务类"""
    
    def __init__(self):
        self.stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'
        }
    
    def search_documents(
        self,
        query: str,
        filters: Dict[str, Any],
        sort_by: str = 'relevance',
        page: int = 1,
        page_size: int = 20,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        文档搜索
        """
        # 构建基础查询集
        queryset = self._get_base_queryset(user)
        
        # 应用搜索条件
        queryset = self._apply_search_filters(queryset, query, filters)
        
        # 应用排序
        queryset = self._apply_sorting(queryset, sort_by, query)
        
        # 分页
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # 序列化结果
        serializer = DocumentSerializer(page_obj.object_list, many=True)
        
        # 高亮搜索关键词
        highlighted_results = self._highlight_search_terms(
            serializer.data, query
        )
        
        return {
            'results': highlighted_results,
            'total': paginator.count,
            'page': page,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    
    def advanced_search(
        self,
        params: Dict[str, Any],
        sort_by: str = 'created_at',
        page: int = 1,
        page_size: int = 20,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        高级搜索
        """
        # 构建基础查询集
        queryset = self._get_base_queryset(user)
        
        # 应用高级搜索条件
        queryset = self._apply_advanced_filters(queryset, params)
        
        # 应用排序
        if sort_by == 'relevance':
            sort_by = 'created_at'
        queryset = self._apply_sorting(queryset, sort_by)
        
        # 分页
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # 序列化结果
        serializer = DocumentSerializer(page_obj.object_list, many=True)
        
        return {
            'results': serializer.data,
            'total': paginator.count,
            'page': page,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    
    def _get_base_queryset(self, user: Optional[User]):
        """获取基础查询集"""
        queryset = Document.objects.select_related(
            'category', 'uploaded_by'
        ).prefetch_related('tags')
        
        # 权限过滤
        if user and not user.is_staff:
            queryset = queryset.filter(
                Q(uploaded_by=user) | Q(is_public=True) | Q(shared_with=user)
            ).distinct()
        
        return queryset
    
    def _apply_search_filters(self, queryset, query: str, filters: Dict[str, Any]):
        """应用搜索过滤条件"""
        # 处理搜索查询
        if query:
            search_terms = self._extract_search_terms(query)
            search_q = Q()
            
            for term in search_terms:
                term_q = (
                    Q(title__icontains=term) |
                    Q(description__icontains=term) |
                    Q(ocr_text__icontains=term) |
                    Q(tags__name__icontains=term) |
                    Q(category__name__icontains=term)
                )
                search_q &= term_q
            
            queryset = queryset.filter(search_q)
        
        # 应用其他过滤条件
        if filters.get('category'):
            queryset = queryset.filter(category_id=filters['category'])
        
        if filters.get('tags'):
            queryset = queryset.filter(tags__id__in=filters['tags'])
        
        if filters.get('file_type'):
            queryset = queryset.filter(file_type=filters['file_type'])
        
        if filters.get('date_from'):
            queryset = queryset.filter(created_at__gte=filters['date_from'])
        
        if filters.get('date_to'):
            queryset = queryset.filter(created_at__lte=filters['date_to'])
        
        return queryset.distinct()
    
    def _apply_advanced_filters(self, queryset, params: Dict[str, Any]):
        """应用高级搜索过滤条件"""
        if params.get('title'):
            queryset = queryset.filter(title__icontains=params['title'])
        
        if params.get('content'):
            queryset = queryset.filter(
                Q(description__icontains=params['content']) |
                Q(ocr_text__icontains=params['content'])
            )
        
        if params.get('category'):
            queryset = queryset.filter(category_id=params['category'])
        
        if params.get('tags'):
            queryset = queryset.filter(tags__id__in=params['tags'])
        
        if params.get('file_type'):
            queryset = queryset.filter(file_type=params['file_type'])
        
        if params.get('uploaded_by'):
            queryset = queryset.filter(uploaded_by__username__icontains=params['uploaded_by'])
        
        if params.get('date_from'):
            queryset = queryset.filter(created_at__gte=params['date_from'])
        
        if params.get('date_to'):
            queryset = queryset.filter(created_at__lte=params['date_to'])
        
        if params.get('file_size_min'):
            queryset = queryset.filter(file_size__gte=params['file_size_min'])
        
        if params.get('file_size_max'):
            queryset = queryset.filter(file_size__lte=params['file_size_max'])
        
        return queryset.distinct()
    
    def _apply_sorting(self, queryset, sort_by: str, query: str = None):
        """应用排序"""
        if sort_by == 'relevance' and query:
            # 相关性排序
            search_terms = self._extract_search_terms(query)
            
            # 计算相关性分数
            relevance_score = Case(
                # 标题完全匹配
                When(title__iexact=query, then=100),
                # 标题包含查询
                When(title__icontains=query, then=80),
                # 描述包含查询
                When(description__icontains=query, then=60),
                # OCR文本包含查询
                When(ocr_text__icontains=query, then=40),
                # 标签匹配
                When(tags__name__icontains=query, then=30),
                # 分类匹配
                When(category__name__icontains=query, then=20),
                default=0,
                output_field=IntegerField()
            )
            
            queryset = queryset.annotate(
                relevance=relevance_score
            ).order_by('-relevance', '-view_count', '-created_at')
            
        elif sort_by == 'created_at':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'updated_at':
            queryset = queryset.order_by('-updated_at')
        elif sort_by == 'view_count':
            queryset = queryset.order_by('-view_count', '-created_at')
        elif sort_by == 'download_count':
            queryset = queryset.order_by('-download_count', '-created_at')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """提取搜索词"""
        # 清理查询字符串
        query = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', query)
        
        # 分词
        terms = query.split()
        
        # 过滤停用词和短词
        filtered_terms = [
            term for term in terms
            if len(term) > 1 and term.lower() not in self.stop_words
        ]
        
        return filtered_terms
    
    def _highlight_search_terms(self, results: List[Dict], query: str) -> List[Dict]:
        """高亮搜索关键词"""
        if not query:
            return results
        
        search_terms = self._extract_search_terms(query)
        
        for result in results:
            # 高亮标题
            if result.get('title'):
                result['title'] = self._highlight_text(result['title'], search_terms)
            
            # 高亮描述
            if result.get('description'):
                result['description'] = self._highlight_text(result['description'], search_terms)
            
            # 生成摘要（从OCR文本中提取包含关键词的片段）
            if result.get('ocr_text'):
                result['summary'] = self._generate_summary(result['ocr_text'], search_terms)
        
        return results
    
    def _highlight_text(self, text: str, terms: List[str]) -> str:
        """高亮文本中的关键词"""
        if not text or not terms:
            return text
        
        highlighted_text = text
        for term in terms:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            highlighted_text = pattern.sub(
                f'<mark>{term}</mark>',
                highlighted_text
            )
        
        return highlighted_text
    
    def _generate_summary(self, text: str, terms: List[str], max_length: int = 200) -> str:
        """生成包含关键词的摘要"""
        if not text or not terms:
            return text[:max_length] + '...' if len(text) > max_length else text
        
        # 查找包含关键词的句子
        sentences = re.split(r'[。！？\.\!\?]', text)
        relevant_sentences = []
        
        for sentence in sentences:
            for term in terms:
                if term.lower() in sentence.lower():
                    relevant_sentences.append(sentence.strip())
                    break
        
        if relevant_sentences:
            summary = '。'.join(relevant_sentences[:2])
            if len(summary) > max_length:
                summary = summary[:max_length] + '...'
            return self._highlight_text(summary, terms)
        
        # 如果没有找到相关句子，返回开头部分
        summary = text[:max_length] + '...' if len(text) > max_length else text
        return self._highlight_text(summary, terms)