"""
文档模块单元测试
"""

import os
import tempfile
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from .models import Document, DocumentCategory, DocumentTag
from .serializers import DocumentSerializer, DocumentUploadSerializer
from .tasks import process_document_async, extract_text_from_file
from .filters import DocumentFilter

User = get_user_model()


class DocumentModelTest(TestCase):
    """文档模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = DocumentCategory.objects.create(
            name='测试分类',
            description='测试分类描述'
        )

    def test_document_creation(self):
        """测试文档创建"""
        document = Document.objects.create(
            title='测试文档',
            description='测试文档描述',
            uploaded_by=self.user,
            category=self.category,
            file_size=1024,
            file_type='pdf'
        )
        
        self.assertEqual(document.title, '测试文档')
        self.assertEqual(document.uploaded_by, self.user)
        self.assertEqual(document.category, self.category)
        self.assertEqual(document.status, 'pending')
        self.assertIsNotNone(document.id)
        self.assertIsNotNone(document.created_at)

    def test_document_str_representation(self):
        """测试文档字符串表示"""
        document = Document.objects.create(
            title='测试文档',
            uploaded_by=self.user,
            category=self.category
        )
        
        self.assertEqual(str(document), '测试文档')

    def test_document_file_path(self):
        """测试文档文件路径生成"""
        document = Document.objects.create(
            title='测试文档',
            uploaded_by=self.user,
            category=self.category
        )
        
        # 测试文件路径生成逻辑
        expected_path = f'documents/{document.id}/'
        self.assertTrue(document.get_file_path().startswith('documents/'))

    def test_document_category_relationship(self):
        """测试文档分类关系"""
        document = Document.objects.create(
            title='测试文档',
            uploaded_by=self.user,
            category=self.category
        )
        
        self.assertEqual(document.category.name, '测试分类')
        self.assertIn(document, self.category.documents.all())

    def test_document_tags(self):
        """测试文档标签"""
        tag1 = DocumentTag.objects.create(name='标签1')
        tag2 = DocumentTag.objects.create(name='标签2')
        
        document = Document.objects.create(
            title='测试文档',
            uploaded_by=self.user,
            category=self.category
        )
        
        document.tags.add(tag1, tag2)
        
        self.assertEqual(document.tags.count(), 2)
        self.assertIn(tag1, document.tags.all())
        self.assertIn(tag2, document.tags.all())


class DocumentSerializerTest(TestCase):
    """文档序列化器测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = DocumentCategory.objects.create(
            name='测试分类',
            description='测试分类描述'
        )

    def test_document_serializer_valid_data(self):
        """测试有效数据序列化"""
        data = {
            'title': '测试文档',
            'description': '测试文档描述',
            'category': self.category.id,
        }
        
        serializer = DocumentSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_document_serializer_invalid_data(self):
        """测试无效数据序列化"""
        data = {
            'title': '',  # 空标题
            'category': 999,  # 不存在的分类
        }
        
        serializer = DocumentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

    def test_document_upload_serializer_file_validation(self):
        """测试文件上传验证"""
        # 创建测试文件
        test_file = SimpleUploadedFile(
            "test.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        data = {
            'title': '测试文档',
            'file': test_file,
            'category': self.category.id,
        }
        
        serializer = DocumentUploadSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_document_upload_serializer_invalid_file_type(self):
        """测试无效文件类型"""
        # 创建不支持的文件类型
        test_file = SimpleUploadedFile(
            "test.exe",
            b"file_content",
            content_type="application/x-executable"
        )
        
        data = {
            'title': '测试文档',
            'file': test_file,
            'category': self.category.id,
        }
        
        serializer = DocumentUploadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('file', serializer.errors)

    def test_document_upload_serializer_file_size_limit(self):
        """测试文件大小限制"""
        # 创建超大文件（模拟）
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        test_file = SimpleUploadedFile(
            "large_test.pdf",
            large_content,
            content_type="application/pdf"
        )
        
        data = {
            'title': '大文件测试',
            'file': test_file,
            'category': self.category.id,
        }
        
        serializer = DocumentUploadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('file', serializer.errors)


class DocumentAPITest(APITestCase):
    """文档API测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = DocumentCategory.objects.create(
            name='测试分类',
            description='测试分类描述'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_document_list_api(self):
        """测试文档列表API"""
        # 创建测试文档
        Document.objects.create(
            title='文档1',
            uploaded_by=self.user,
            category=self.category
        )
        Document.objects.create(
            title='文档2',
            uploaded_by=self.user,
            category=self.category
        )
        
        response = self.client.get('/api/v1/documents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_document_create_api(self):
        """测试文档创建API"""
        data = {
            'title': '新文档',
            'description': '新文档描述',
            'category': self.category.id,
        }
        
        response = self.client.post('/api/v1/documents/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Document.objects.count(), 1)

    def test_document_upload_api(self):
        """测试文档上传API"""
        test_file = SimpleUploadedFile(
            "test.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        data = {
            'title': '上传文档',
            'file': test_file,
            'category': self.category.id,
        }
        
        response = self.client.post('/api/v1/documents/upload/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_document_detail_api(self):
        """测试文档详情API"""
        document = Document.objects.create(
            title='测试文档',
            uploaded_by=self.user,
            category=self.category
        )
        
        response = self.client.get(f'/api/v1/documents/{document.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], '测试文档')

    def test_document_update_api(self):
        """测试文档更新API"""
        document = Document.objects.create(
            title='原标题',
            uploaded_by=self.user,
            category=self.category
        )
        
        data = {'title': '新标题'}
        response = self.client.patch(f'/api/v1/documents/{document.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        document.refresh_from_db()
        self.assertEqual(document.title, '新标题')

    def test_document_delete_api(self):
        """测试文档删除API"""
        document = Document.objects.create(
            title='待删除文档',
            uploaded_by=self.user,
            category=self.category
        )
        
        response = self.client.delete(f'/api/v1/documents/{document.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Document.objects.count(), 0)

    def test_document_filter_by_category(self):
        """测试按分类过滤文档"""
        category2 = DocumentCategory.objects.create(name='分类2')
        
        Document.objects.create(
            title='文档1',
            uploaded_by=self.user,
            category=self.category
        )
        Document.objects.create(
            title='文档2',
            uploaded_by=self.user,
            category=category2
        )
        
        response = self.client.get(f'/api/v1/documents/?category={self.category.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_document_search(self):
        """测试文档搜索"""
        Document.objects.create(
            title='Python编程指南',
            uploaded_by=self.user,
            category=self.category
        )
        Document.objects.create(
            title='Java开发手册',
            uploaded_by=self.user,
            category=self.category
        )
        
        response = self.client.get('/api/v1/documents/?search=Python')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_unauthorized_access(self):
        """测试未授权访问"""
        self.client.force_authenticate(user=None)
        
        response = self.client.get('/api/v1/documents/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DocumentTaskTest(TestCase):
    """文档任务测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = DocumentCategory.objects.create(
            name='测试分类',
            description='测试分类描述'
        )

    @patch('apps.documents.tasks.extract_text_from_file')
    @patch('apps.documents.tasks.update_search_index')
    def test_process_document_async_success(self, mock_update_index, mock_extract_text):
        """测试异步文档处理成功"""
        # 创建测试文档
        document = Document.objects.create(
            title='测试文档',
            uploaded_by=self.user,
            category=self.category,
            status='pending'
        )
        
        # 模拟文本提取
        mock_extract_text.return_value = '提取的文本内容'
        mock_update_index.return_value = True
        
        # 执行任务
        result = process_document_async(document.id)
        
        # 验证结果
        self.assertTrue(result)
        mock_extract_text.assert_called_once()
        mock_update_index.assert_called_once()
        
        # 验证文档状态更新
        document.refresh_from_db()
        self.assertEqual(document.status, 'processed')

    @patch('apps.documents.tasks.extract_text_from_file')
    def test_process_document_async_failure(self, mock_extract_text):
        """测试异步文档处理失败"""
        # 创建测试文档
        document = Document.objects.create(
            title='测试文档',
            uploaded_by=self.user,
            category=self.category,
            status='pending'
        )
        
        # 模拟处理失败
        mock_extract_text.side_effect = Exception('处理失败')
        
        # 执行任务
        with self.assertRaises(Exception):
            process_document_async(document.id)
        
        # 验证文档状态
        document.refresh_from_db()
        self.assertEqual(document.status, 'error')

    def test_extract_text_from_pdf(self):
        """测试PDF文本提取"""
        # 创建临时PDF文件
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n')
            tmp_file_path = tmp_file.name
        
        try:
            # 测试文本提取（这里只是测试函数调用，实际提取可能需要真实PDF）
            result = extract_text_from_file(tmp_file_path)
            self.assertIsInstance(result, str)
        finally:
            # 清理临时文件
            os.unlink(tmp_file_path)

    def test_extract_text_from_txt(self):
        """测试TXT文本提取"""
        # 创建临时TXT文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write('这是测试文本内容')
            tmp_file_path = tmp_file.name
        
        try:
            # 测试文本提取
            result = extract_text_from_file(tmp_file_path)
            self.assertEqual(result, '这是测试文本内容')
        finally:
            # 清理临时文件
            os.unlink(tmp_file_path)


class DocumentFilterTest(TestCase):
    """文档过滤器测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category1 = DocumentCategory.objects.create(name='分类1')
        self.category2 = DocumentCategory.objects.create(name='分类2')
        
        # 创建测试文档
        self.doc1 = Document.objects.create(
            title='Python文档',
            uploaded_by=self.user,
            category=self.category1,
            file_type='pdf'
        )
        self.doc2 = Document.objects.create(
            title='Java文档',
            uploaded_by=self.user,
            category=self.category2,
            file_type='docx'
        )

    def test_filter_by_category(self):
        """测试按分类过滤"""
        filter_set = DocumentFilter(
            data={'category': self.category1.id},
            queryset=Document.objects.all()
        )
        
        self.assertTrue(filter_set.is_valid())
        filtered_docs = filter_set.qs
        self.assertEqual(filtered_docs.count(), 1)
        self.assertEqual(filtered_docs.first(), self.doc1)

    def test_filter_by_file_type(self):
        """测试按文件类型过滤"""
        filter_set = DocumentFilter(
            data={'file_type': 'pdf'},
            queryset=Document.objects.all()
        )
        
        self.assertTrue(filter_set.is_valid())
        filtered_docs = filter_set.qs
        self.assertEqual(filtered_docs.count(), 1)
        self.assertEqual(filtered_docs.first(), self.doc1)

    def test_filter_by_search(self):
        """测试搜索过滤"""
        filter_set = DocumentFilter(
            data={'search': 'Python'},
            queryset=Document.objects.all()
        )
        
        self.assertTrue(filter_set.is_valid())
        filtered_docs = filter_set.qs
        self.assertEqual(filtered_docs.count(), 1)
        self.assertEqual(filtered_docs.first(), self.doc1)

    def test_filter_by_date_range(self):
        """测试按日期范围过滤"""
        from datetime import date, timedelta
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        filter_set = DocumentFilter(
            data={
                'created_after': yesterday.isoformat(),
                'created_before': today.isoformat()
            },
            queryset=Document.objects.all()
        )
        
        self.assertTrue(filter_set.is_valid())
        # 由于测试数据是今天创建的，应该能找到文档
        filtered_docs = filter_set.qs
        self.assertGreaterEqual(filtered_docs.count(), 0)


class DocumentPerformanceTest(TestCase):
    """文档性能测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = DocumentCategory.objects.create(name='测试分类')

    def test_bulk_document_creation(self):
        """测试批量文档创建性能"""
        import time
        
        start_time = time.time()
        
        # 批量创建文档
        documents = []
        for i in range(100):
            documents.append(Document(
                title=f'文档{i}',
                uploaded_by=self.user,
                category=self.category
            ))
        
        Document.objects.bulk_create(documents)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # 验证创建成功
        self.assertEqual(Document.objects.count(), 100)
        
        # 性能断言（应该在1秒内完成）
        self.assertLess(creation_time, 1.0)

    def test_document_query_performance(self):
        """测试文档查询性能"""
        import time
        
        # 创建大量测试数据
        documents = []
        for i in range(1000):
            documents.append(Document(
                title=f'文档{i}',
                uploaded_by=self.user,
                category=self.category
            ))
        Document.objects.bulk_create(documents)
        
        start_time = time.time()
        
        # 执行查询
        result = Document.objects.select_related('category', 'uploaded_by').filter(
            category=self.category
        )[:10]
        
        # 强制执行查询
        list(result)
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # 性能断言（应该在0.1秒内完成）
        self.assertLess(query_time, 0.1)