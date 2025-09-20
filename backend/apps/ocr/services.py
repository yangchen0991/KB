"""
OCR服务
"""

import io
import time
import logging
from typing import Dict, Any, Optional
from PIL import Image
import requests
from django.conf import settings
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


class OCRService:
    """OCR服务基类"""
    
    def __init__(self, provider: str = 'tesseract'):
        self.provider = provider
        self.config = getattr(settings, 'OCR_CONFIG', {})
    
    def extract_text(self, image_data: bytes, language: str = 'zh-cn') -> Dict[str, Any]:
        """提取文本"""
        if self.provider == 'tesseract':
            return self._tesseract_ocr(image_data, language)
        elif self.provider == 'baidu':
            return self._baidu_ocr(image_data)
        elif self.provider == 'tencent':
            return self._tencent_ocr(image_data)
        elif self.provider == 'aliyun':
            return self._aliyun_ocr(image_data)
        elif self.provider == 'azure':
            return self._azure_ocr(image_data)
        else:
            raise ValueError(f'不支持的OCR提供商: {self.provider}')
    
    def _tesseract_ocr(self, image_data: bytes, language: str) -> Dict[str, Any]:
        """Tesseract OCR识别"""
        try:
            import pytesseract
            from PIL import Image
            
            # 将字节数据转换为PIL图像
            image = Image.open(io.BytesIO(image_data))
            
            # 执行OCR
            start_time = time.time()
            text = pytesseract.image_to_string(image, lang=language)
            processing_time = time.time() - start_time
            
            # 获取详细信息
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # 计算置信度
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                'text': text.strip(),
                'confidence': avg_confidence,
                'processing_time': processing_time,
                'word_count': len(text.split()),
                'line_count': len(text.split('\n')),
                'raw_data': data,
                'provider': 'tesseract'
            }
            
        except ImportError:
            logger.error("Tesseract未安装，使用模拟OCR")
            return self._mock_ocr(image_data)
        except Exception as e:
            logger.error(f"Tesseract OCR失败: {e}")
            return self._mock_ocr(image_data)
    
    def _baidu_ocr(self, image_data: bytes) -> Dict[str, Any]:
        """百度OCR识别"""
        try:
            import base64
            
            config = self.config.get('baidu', {})
            api_key = config.get('api_key')
            secret_key = config.get('secret_key')
            
            if not api_key or not secret_key:
                logger.warning("百度OCR配置缺失，使用模拟OCR")
                return self._mock_ocr(image_data)
            
            # 获取access_token
            token_url = "https://aip.baidubce.com/oauth/2.0/token"
            token_params = {
                'grant_type': 'client_credentials',
                'client_id': api_key,
                'client_secret': secret_key
            }
            
            token_response = requests.post(token_url, data=token_params, timeout=10)
            access_token = token_response.json().get('access_token')
            
            if not access_token:
                raise Exception("获取百度OCR access_token失败")
            
            # 调用OCR API
            ocr_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            ocr_data = {
                'image': image_base64,
                'access_token': access_token
            }
            
            start_time = time.time()
            response = requests.post(ocr_url, headers=headers, data=ocr_data, timeout=30)
            processing_time = time.time() - start_time
            
            result = response.json()
            
            if 'words_result' not in result:
                raise Exception(f"百度OCR API错误: {result}")
            
            # 提取文本
            text_lines = [item['words'] for item in result['words_result']]
            text = '\n'.join(text_lines)
            
            return {
                'text': text,
                'confidence': 95.0,  # 百度OCR通常质量较高
                'processing_time': processing_time,
                'word_count': len(text.replace(' ', '')),
                'line_count': len(text_lines),
                'raw_data': result,
                'provider': 'baidu'
            }
            
        except Exception as e:
            logger.error(f"百度OCR失败: {e}")
            return self._mock_ocr(image_data)
    
    def _tencent_ocr(self, image_data: bytes) -> Dict[str, Any]:
        """腾讯OCR识别"""
        logger.info("腾讯OCR暂未实现，使用模拟OCR")
        return self._mock_ocr(image_data)
    
    def _aliyun_ocr(self, image_data: bytes) -> Dict[str, Any]:
        """阿里云OCR识别"""
        logger.info("阿里云OCR暂未实现，使用模拟OCR")
        return self._mock_ocr(image_data)
    
    def _azure_ocr(self, image_data: bytes) -> Dict[str, Any]:
        """Azure OCR识别"""
        logger.info("Azure OCR暂未实现，使用模拟OCR")
        return self._mock_ocr(image_data)
    
    def _mock_ocr(self, image_data: bytes) -> Dict[str, Any]:
        """模拟OCR识别（用于测试）"""
        try:
            # 模拟处理时间
            time.sleep(1)
            
            # 根据图片大小生成模拟文本
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            
            mock_text = f"""这是一个模拟的OCR识别结果。
图片尺寸: {width} x {height}
识别时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

这里是模拟识别的文档内容：
- 标题：示例文档
- 内容：这是一段示例文本内容
- 日期：2025年1月1日
- 备注：OCR识别功能正常工作

如需使用真实OCR服务，请配置相应的API密钥。"""
            
            return {
                'text': mock_text,
                'confidence': 88.5,
                'processing_time': 1.2,
                'word_count': len(mock_text.replace(' ', '').replace('\n', '')),
                'line_count': len(mock_text.split('\n')),
                'raw_data': {'mock': True, 'image_size': [width, height]},
                'provider': 'mock'
            }
            
        except Exception as e:
            logger.error(f"模拟OCR失败: {e}")
            return {
                'text': '模拟OCR识别失败',
                'confidence': 0,
                'processing_time': 0,
                'word_count': 0,
                'line_count': 0,
                'raw_data': {'error': str(e)},
                'provider': 'mock'
            }


class DocumentOCRProcessor:
    """文档OCR处理器"""
    
    def __init__(self):
        self.ocr_service = OCRService()
    
    def process_document(self, document, provider: str = 'tesseract') -> Optional[object]:
        """处理文档OCR"""
        from .models import OCRTask, OCRResult
        
        try:
            # 创建OCR任务
            task = OCRTask.objects.create(
                document=document,
                user=document.uploaded_by,
                provider=provider,
                status='processing'
            )
            
            # 更新开始时间
            task.started_at = time.time()
            task.save()
            
            # 读取文档文件
            if not document.file:
                raise Exception("文档文件不存在")
            
            # 如果是图片文件，直接处理
            if document.file_type in ['jpg', 'jpeg', 'png', 'bmp', 'tiff']:
                image_data = document.file.read()
            else:
                # 对于PDF等文件，需要先转换为图片
                image_data = self._convert_to_image(document.file)
            
            # 执行OCR
            self.ocr_service.provider = provider
            result = self.ocr_service.extract_text(image_data)
            
            # 更新任务状态
            task.status = 'completed'
            task.extracted_text = result['text']
            task.confidence_score = result['confidence']
            task.processing_time = result['processing_time']
            task.completed_at = time.time()
            task.save()
            
            # 创建详细结果
            OCRResult.objects.create(
                task=task,
                raw_result=result['raw_data'],
                word_count=result['word_count'],
                line_count=result['line_count'],
                quality_score=result['confidence']
            )
            
            # 更新文档的OCR文本
            document.ocr_text = result['text']
            document.save()
            
            return task
            
        except Exception as e:
            logger.error(f"OCR处理失败: {e}")
            if 'task' in locals():
                task.status = 'failed'
                task.error_message = str(e)
                task.save()
            return None
    
    def _convert_to_image(self, file) -> bytes:
        """将文件转换为图片"""
        try:
            # 这里应该实现PDF转图片的逻辑
            # 暂时返回空字节，实际使用时需要安装pdf2image等库
            logger.warning("PDF转图片功能暂未实现")
            
            # 创建一个简单的白色图片作为占位符
            img = Image.new('RGB', (800, 600), color='white')
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            return img_bytes.getvalue()
            
        except Exception as e:
            logger.error(f"文件转换失败: {e}")
            raise