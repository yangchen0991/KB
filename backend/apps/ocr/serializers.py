"""
OCR序列化器
"""

from rest_framework import serializers
from .models import OCRTask, OCRResult


class OCRTaskSerializer(serializers.ModelSerializer):
    """OCR任务序列化器"""
    
    document_title = serializers.CharField(source='document.title', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    
    class Meta:
        model = OCRTask
        fields = [
            'id', 'document', 'document_title', 'user', 'user_name',
            'status', 'status_display', 'provider', 'provider_display',
            'extracted_text', 'confidence_score', 'language',
            'processing_time', 'error_message',
            'created_at', 'started_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'user', 'extracted_text', 'confidence_score',
            'processing_time', 'error_message', 'created_at',
            'started_at', 'completed_at'
        ]


class OCRResultSerializer(serializers.ModelSerializer):
    """OCR结果序列化器"""
    
    task_info = OCRTaskSerializer(source='task', read_only=True)
    
    class Meta:
        model = OCRResult
        fields = [
            'id', 'task', 'task_info', 'raw_result', 'structured_data',
            'text_blocks', 'word_count', 'line_count',
            'quality_score', 'blur_score', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class OCRRequestSerializer(serializers.Serializer):
    """OCR请求序列化器"""
    
    document_id = serializers.UUIDField(required=True)
    provider = serializers.ChoiceField(
        choices=OCRTask.PROVIDER_CHOICES,
        default='tesseract'
    )
    language = serializers.CharField(max_length=10, default='zh-cn')
    
    def validate_document_id(self, value):
        """验证文档ID"""
        from apps.documents.models import Document
        
        try:
            document = Document.objects.get(id=value)
            return value
        except Document.DoesNotExist:
            raise serializers.ValidationError("文档不存在")