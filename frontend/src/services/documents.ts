import { api } from './api';
import { Document, DocumentUpload, SearchParams, SearchResult } from '@/types';

export const documentsService = {
  // 获取文档列表
  async getDocuments(params?: {
    page?: number;
    page_size?: number;
    search?: string;
    category?: string;
    tags?: string[];
  }): Promise<{
    results: Document[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  }> {
    const response = await api.get('/documents/', { params });
    return response.data;
  },

  // 获取单个文档
  async getDocument(id: string): Promise<Document> {
    const response = await api.get(`/documents/${id}/`);
    return response.data;
  },

  // 上传文档
  async uploadDocument(data: DocumentUpload): Promise<Document> {
    const formData = new FormData();
    
    formData.append('file', data.file);
    formData.append('title', data.title);
    
    if (data.description) {
      formData.append('description', data.description);
    }
    
    if (data.category) {
      formData.append('category', data.category);
    }
    
    if (data.tags && data.tags.length > 0) {
      data.tags.forEach(tag => {
        formData.append('tags', tag);
      });
    }
    
    if (data.is_public !== undefined) {
      formData.append('is_public', data.is_public.toString());
    }

    const response = await api.post('/documents/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: data.onProgress,
    });
    
    return response.data;
  },

  // 更新文档
  async updateDocument(id: string, data: Partial<Document>): Promise<Document> {
    const response = await api.patch(`/documents/${id}/`, data);
    return response.data;
  },

  // 删除文档
  async deleteDocument(id: string): Promise<void> {
    await api.delete(`/documents/${id}/`);
  },

  // 下载文档
  async downloadDocument(id: string): Promise<Blob> {
    const response = await api.get(`/documents/${id}/download/`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // 预览文档
  async previewDocument(id: string): Promise<{
    document_id: string;
    title: string;
    file_type: string;
    preview_data: any;
    ocr_text: string;
    page_count: number;
  }> {
    const response = await api.get(`/documents/${id}/preview/`);
    return response.data;
  },

  // 搜索文档
  async searchDocuments(params: SearchParams): Promise<SearchResult> {
    const response = await api.get('/documents/search/', { params });
    return response.data;
  },

  // 触发OCR处理
  async processOCR(id: string, provider: string = 'tesseract'): Promise<{
    message: string;
    task_id: string;
    status: string;
  }> {
    const response = await api.post(`/documents/${id}/ocr_process/`, {
      provider,
    });
    return response.data;
  },

  // 获取分类列表
  async getCategories(): Promise<{
    categories: Array<{
      id: string;
      name: string;
      description: string;
      color: string;
      document_count: number;
    }>;
  }> {
    const response = await api.get('/documents/categories/');
    return response.data;
  },

  // 获取标签列表
  async getTags(): Promise<{
    tags: Array<{
      id: string;
      name: string;
      color: string;
      document_count: number;
    }>;
  }> {
    const response = await api.get('/documents/tags/');
    return response.data;
  },
};