"""
搜索模块单元测试
"""

import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from apps.documents.models import Document, DocumentCategory
from .models import SearchQuery, PopularSearch, SearchIndex
from .serializers import SearchQuerySerializer, PopularSearchSerializer
from .services import SearchService

User = get_user_model()


class SearchModelTest(TestCase):
    """搜索模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_search_query_creation(self):
        """测试搜索查询创建"""
        query = SearchQuery.objects.create(
            query_text='Python编程',
            user=self.user,
            results_count=10,
            response_time=0.5
        )
        
        self.assertEqual(query.query_text, 'Python编程')
        self.assertEqual(query.user, self.user)
        self.assertEqual(query.results_count, 10)
        self.assertEqual(query.response_time, 0.5)
        self.assertIsNotNone(query.id)
        self.assertIsNotNone(query.created_at)

    def test_search_query_str_representation(self):
        """测试搜索查询字符串表示"""
        query = SearchQuery.objects.create(
            query_text='Django框架',
            user=self.user
        )
        
        self.assertEqual(str(query), 'Django框架')

    def test_popular_search_creation(self):
        """测试热门搜索创建"""
        popular = PopularSearch.objects.create(
            query_text='机器学习',
            search_count=100,
            trend_score=0.8
        )
        
        self.assertEqual(popular.query_text, '机器学习')
        self.assertEqual(popular.search_count, 100)
        self.assertEqual(popular.trend_score, 0.8)

    def test_popular_search_increment(self):
        """测试热门搜索计数增加"""
        popular = PopularSearch.objects.create(
            query_text='人工智能',
            search_count=50
        )
        
        # 模拟搜索计数增加
        popular.search_count += 1
        popular.save()
        
        self.assertEqual(popular.search_count, 51)

    def test_search_index_creation(self):
        """测试搜索索引创建"""
        category = DocumentCategory.objects.create(name='技术文档')
        document = Document.objects.create(
            title='测试文档',
            uploaded_by=self.user,
            category=category
        )
        
        index = SearchIndex.objects.create(
            document=document,
            content='这是测试文档的内容',
            keywords=['测试', '文档', '内容']
        )
        
        self.assertEqual(index.document, document)
        self.assertEqual(index.content, '这是测试文档的内容')
        self.assertEqual(index.keywords, ['测试', '文档', '内容'])


class SearchSerializerTest(TestCase):
    """搜索序列化器测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_search_query_serializer_valid_data(self):
        """测试搜索查询序列化器有效数据"""
        data = {
            'query_text': 'Python编程',
            'filters': {'category': 'tech'},
            'sort_by': 'relevance'
        }
        
        serializer = SearchQuerySerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_search_query_serializer_invalid_data(self):
        """测试搜索查询序列化器无效数据"""
        data = {
            'query_text': '',  # 空查询
        }
        
        serializer = SearchQuerySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('query_text', serializer.errors)

    def test_popular_search_serializer(self):
        """测试热门搜索序列化器"""
        popular = PopularSearch.objects.create(
            query_text='深度学习',
            search_count=200,
            trend_score=0.9
        )
        
        serializer = PopularSearchSerializer(popular)
        data = serializer.data
        
        self.assertEqual(data['query_text'], '深度学习')
        self.assertEqual(data['search_count'], 200)
        self.assertEqual(data['trend_score'], 0.9)


class SearchAPITest(APITestCase):
    """搜索API测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # 创建测试数据
        self.category = DocumentCategory.objects.create(name='技术文档')
        self.document = Document.objects.create(
            title='Python编程指南',
            description='详细的Python编程教程',
            uploaded_by=self.user,
            category=self.category
        )

    def test_search_api_basic(self):
        """测试基本搜索API"""
        data = {
            'query': 'Python',
            'page': 1,
            'page_size': 10
        }
        
        response = self.client.post('/api/v1/search/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('total_count', response.data)
        self.assertIn('page', response.data)

    def test_search_api_with_filters(self):
        """测试带过滤器的搜索API"""
        data = {
            'query': 'Python',
            'filters': {
                'category': self.category.id,
                'file_type': 'pdf'
            },
            'page': 1,
            'page_size': 10
        }
        
        response = self.client.post('/api/v1/search/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_api_sorting(self):
        """测试搜索结果排序"""
        data = {
            'query': 'Python',
            'sort_by': 'created_at',
            'sort_order': 'desc'
        }
        
        response = self.client.post('/api/v1/search/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_suggestions_api(self):
        """测试搜索建议API"""
        # 创建一些搜索历史
        SearchQuery.objects.create(
            query_text='Python编程',
            user=self.user,
            results_count=10
        )
        SearchQuery.objects.create(
            query_text='Python框架',
            user=self.user,
            results_count=5
        )
        
        response = self.client.get('/api/v1/search/suggestions/?q=Python')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('suggestions', response.data)

    def test_popular_searches_api(self):
        """测试热门搜索API"""
        # 创建热门搜索
        PopularSearch.objects.create(
            query_text='机器学习',
            search_count=100,
            trend_score=0.8
        )
        PopularSearch.objects.create(
            query_text='深度学习',
            search_count=80,
            trend_score=0.7
        )
        
        response = self.client.get('/api/v1/search/popular/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_search_analytics_api(self):
        """测试搜索分析API"""
        # 创建搜索历史
        SearchQuery.objects.create(
            query_text='Python',
            user=self.user,
            results_count=10
        )
        SearchQuery.objects.create(
            query_text='Django',
            user=self.user,
            results_count=5
        )
        
        response = self.client.get('/api/v1/search/analytics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_searches', response.data)
        self.assertIn('avg_response_time', response.data)

    def test_advanced_search_api(self):
        """测试高级搜索API"""
        data = {
            'query': 'Python',
            'title_only': True,
            'exact_phrase': False,
            'date_range': {
                'start': '2024-01-01',
                'end': '2024-12-31'
            },
            'file_types': ['pdf', 'docx'],
            'categories': [self.category.id]
        }
        
        response = self.client.post('/api/v1/search/advanced/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_history_api(self):
        """测试搜索历史API"""
        # 创建搜索历史
        SearchQuery.objects.create(
            query_text='Python编程',
            user=self.user,
            results_count=10
        )
        
        response = self.client.get('/api/v1/search/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_clear_search_history_api(self):
        """测试清除搜索历史API"""
        # 创建搜索历史
        SearchQuery.objects.create(
            query_text='Python编程',
            user=self.user,
            results_count=10
        )
        
        response = self.client.delete('/api/v1/search/history/clear/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # 验证历史已清除
        self.assertEqual(SearchQuery.objects.filter(user=self.user).count(), 0)

    def test_unauthorized_search_access(self):
        """测试未授权搜索访问"""
        self.client.force_authenticate(user=None)
        
        data = {'query': 'Python'}
        response = self.client.post('/api/v1/search/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SearchServiceTest(TestCase):
    """搜索服务测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = DocumentCategory.objects.create(name='技术文档')
        self.document = Document.objects.create(
            title='Python编程指南',
            description='详细的Python编程教程',
            uploaded_by=self.user,
            category=self.category
        )
        self.search_service = SearchService()

    @patch('apps.search.services.SearchService._execute_search')
    def test_search_documents_success(self, mock_execute_search):
        """测试文档搜索成功"""
        # 模拟搜索结果
        mock_execute_search.return_value = {
            'results': [
                {
                    'id': str(self.document.id),
                    'title': 'Python编程指南',
                    'content': '详细的Python编程教程',
                    'score': 0.95
                }
            ],
            'total_count': 1,
            'took': 50
        }
        
        result = self.search_service.search_documents(
            query='Python',
            user=self.user,
            page=1,
            page_size=10
        )
        
        self.assertEqual(result['total_count'], 1)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['title'], 'Python编程指南')

    def test_build_search_query(self):
        """测试构建搜索查询"""
        query_dict = self.search_service._build_search_query(
            query='Python编程',
            filters={'category': self.category.id},
            sort_by='relevance'
        )
        
        self.assertIn('query', query_dict)
        self.assertIn('filter', query_dict)
        self.assertIn('sort', query_dict)

    def test_highlight_keywords(self):
        """测试关键词高亮"""
        content = '这是一个关于Python编程的文档'
        keywords = ['Python', '编程']
        
        highlighted = self.search_service._highlight_keywords(content, keywords)
        
        self.assertIn('<mark>Python</mark>', highlighted)
        self.assertIn('<mark>编程</mark>', highlighted)

    def test_calculate_relevance_score(self):
        """测试相关性评分计算"""
        document_data = {
            'title': 'Python编程指南',
            'content': '这是一个详细的Python编程教程',
            'category': '技术文档'
        }
        
        score = self.search_service._calculate_relevance_score(
            document_data, 'Python编程'
        )
        
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_update_search_analytics(self):
        """测试更新搜索分析"""
        # 执行搜索分析更新
        self.search_service._update_search_analytics(
            query='Python',
            user=self.user,
            results_count=10,
            response_time=0.5
        )
        
        # 验证搜索查询记录
        query_record = SearchQuery.objects.filter(
            query_text='Python',
            user=self.user
        ).first()
        
        self.assertIsNotNone(query_record)
        self.assertEqual(query_record.results_count, 10)
        self.assertEqual(query_record.response_time, 0.5)

    def test_get_search_suggestions(self):
        """测试获取搜索建议"""
        # 创建搜索历史
        SearchQuery.objects.create(
            query_text='Python编程',
            user=self.user,
            results_count=10
        )
        SearchQuery.objects.create(
            query_text='Python框架',
            user=self.user,
            results_count=5
        )
        
        suggestions = self.search_service.get_search_suggestions('Python')
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)

    def test_get_popular_searches(self):
        """测试获取热门搜索"""
        # 创建热门搜索
        PopularSearch.objects.create(
            query_text='机器学习',
            search_count=100,
            trend_score=0.8
        )
        PopularSearch.objects.create(
            query_text='深度学习',
            search_count=80,
            trend_score=0.7
        )
        
        popular_searches = self.search_service.get_popular_searches(limit=10)
        
        self.assertIsInstance(popular_searches, list)
        self.assertEqual(len(popular_searches), 2)
        # 验证按搜索次数排序
        self.assertEqual(popular_searches[0]['query_text'], '机器学习')

    def test_advanced_search(self):
        """测试高级搜索"""
        search_params = {
            'query': 'Python',
            'title_only': True,
            'exact_phrase': False,
            'date_range': {
                'start': '2024-01-01',
                'end': '2024-12-31'
            },
            'file_types': ['pdf', 'docx'],
            'categories': [self.category.id]
        }
        
        # 这里只测试参数处理，实际搜索需要Elasticsearch
        query_dict = self.search_service._build_advanced_search_query(search_params)
        
        self.assertIn('query', query_dict)
        self.assertIn('filter', query_dict)


class SearchPerformanceTest(TestCase):
    """搜索性能测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.search_service = SearchService()

    def test_bulk_search_query_creation(self):
        """测试批量搜索查询创建性能"""
        import time
        
        start_time = time.time()
        
        # 批量创建搜索查询
        queries = []
        for i in range(100):
            queries.append(SearchQuery(
                query_text=f'查询{i}',
                user=self.user,
                results_count=10,
                response_time=0.1
            ))
        
        SearchQuery.objects.bulk_create(queries)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # 验证创建成功
        self.assertEqual(SearchQuery.objects.count(), 100)
        
        # 性能断言（应该在1秒内完成）
        self.assertLess(creation_time, 1.0)

    def test_search_query_performance(self):
        """测试搜索查询性能"""
        import time
        
        # 创建大量测试数据
        queries = []
        for i in range(1000):
            queries.append(SearchQuery(
                query_text=f'查询{i}',
                user=self.user,
                results_count=10,
                response_time=0.1
            ))
        SearchQuery.objects.bulk_create(queries)
        
        start_time = time.time()
        
        # 执行查询
        result = SearchQuery.objects.filter(user=self.user).order_by('-created_at')[:10]
        
        # 强制执行查询
        list(result)
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # 性能断言（应该在0.1秒内完成）
        self.assertLess(query_time, 0.1)

    def test_popular_search_aggregation_performance(self):
        """测试热门搜索聚合性能"""
        import time
        
        # 创建大量搜索查询
        queries = []
        for i in range(1000):
            queries.append(SearchQuery(
                query_text=f'Python{i % 10}',  # 创建重复查询
                user=self.user,
                results_count=10,
                response_time=0.1
            ))
        SearchQuery.objects.bulk_create(queries)
        
        start_time = time.time()
        
        # 执行聚合查询
        from django.db.models import Count
        popular_queries = SearchQuery.objects.values('query_text').annotate(
            search_count=Count('id')
        ).order_by('-search_count')[:10]
        
        # 强制执行查询
        list(popular_queries)
        
        end_time = time.time()
        aggregation_time = end_time - start_time
        
        # 性能断言（应该在0.5秒内完成）
        self.assertLess(aggregation_time, 0.5)


class SearchIntegrationTest(APITestCase):
    """搜索集成测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # 创建测试数据
        self.category = DocumentCategory.objects.create(name='技术文档')
        self.documents = []
        for i in range(5):
            doc = Document.objects.create(
                title=f'Python文档{i}',
                description=f'这是第{i}个Python编程文档',
                uploaded_by=self.user,
                category=self.category
            )
            self.documents.append(doc)

    def test_end_to_end_search_workflow(self):
        """测试端到端搜索工作流"""
        # 1. 执行搜索
        search_data = {
            'query': 'Python',
            'page': 1,
            'page_size': 10
        }
        
        search_response = self.client.post('/api/v1/search/', search_data)
        self.assertEqual(search_response.status_code, status.HTTP_200_OK)
        
        # 2. 检查搜索历史
        history_response = self.client.get('/api/v1/search/history/')
        self.assertEqual(history_response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(history_response.data['results']), 0)
        
        # 3. 获取搜索建议
        suggestions_response = self.client.get('/api/v1/search/suggestions/?q=Py')
        self.assertEqual(suggestions_response.status_code, status.HTTP_200_OK)
        
        # 4. 查看搜索分析
        analytics_response = self.client.get('/api/v1/search/analytics/')
        self.assertEqual(analytics_response.status_code, status.HTTP_200_OK)
        self.assertGreater(analytics_response.data['total_searches'], 0)

    def test_search_with_multiple_filters(self):
        """测试多重过滤器搜索"""
        search_data = {
            'query': 'Python',
            'filters': {
                'category': self.category.id,
                'created_after': '2024-01-01',
                'created_before': '2024-12-31'
            },
            'sort_by': 'created_at',
            'sort_order': 'desc'
        }
        
        response = self.client.post('/api/v1/search/', search_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证结果按创建时间降序排列
        results = response.data['results']
        if len(results) > 1:
            for i in range(len(results) - 1):
                self.assertGreaterEqual(
                    results[i]['created_at'],
                    results[i + 1]['created_at']
                )

    def test_search_pagination(self):
        """测试搜索分页"""
        # 第一页
        page1_response = self.client.post('/api/v1/search/', {
            'query': 'Python',
            'page': 1,
            'page_size': 2
        })
        self.assertEqual(page1_response.status_code, status.HTTP_200_OK)
        
        # 第二页
        page2_response = self.client.post('/api/v1/search/', {
            'query': 'Python',
            'page': 2,
            'page_size': 2
        })
        self.assertEqual(page2_response.status_code, status.HTTP_200_OK)
        
        # 验证分页信息
        self.assertEqual(page1_response.data['page'], 1)
        self.assertEqual(page2_response.data['page'], 2)
        self.assertEqual(page1_response.data['page_size'], 2)
        self.assertEqual(page2_response.data['page_size'], 2)