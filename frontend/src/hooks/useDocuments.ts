import { useState, useEffect, useCallback } from 'react';
import { documentService } from '@/services/documents';
import {
  Document,
  DocumentUpload,
  PaginatedResponse,
  SearchRequest,
  SearchResponse,
} from '@/types';

interface UseDocumentsOptions {
  autoFetch?: boolean;
  page?: number;
  pageSize?: number;
  categoryId?: number;
  tags?: string[];
  search?: string;
  ordering?: string;
}

interface UseDocumentsReturn {
  documents: Document[];
  loading: boolean;
  error: string | null;
  pagination: {
    current: number;
    pageSize: number;
    total: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
  fetchDocuments: (options?: UseDocumentsOptions) => Promise<void>;
  uploadDocument: (
    data: DocumentUpload,
    onProgress?: (progress: number) => void,
  ) => Promise<Document>;
  updateDocument: (id: number, data: Partial<Document>) => Promise<Document>;
  deleteDocument: (id: number) => Promise<void>;
  searchDocuments: (request: SearchRequest) => Promise<SearchResponse>;
  refreshDocuments: () => Promise<void>;
}

export const useDocuments = (
  options: UseDocumentsOptions = {},
): UseDocumentsReturn => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    current: options.page || 1,
    pageSize: options.pageSize || 20,
    total: 0,
    hasNext: false,
    hasPrevious: false,
  });

  // 获取文档列表
  const fetchDocuments = useCallback(
    async (fetchOptions: UseDocumentsOptions = {}) => {
      try {
        setLoading(true);
        setError(null);

        const params = {
          page: fetchOptions.page || pagination.current,
          page_size: fetchOptions.pageSize || pagination.pageSize,
          category_id: fetchOptions.categoryId || options.categoryId,
          tags: fetchOptions.tags || options.tags,
          search: fetchOptions.search || options.search,
          ordering: fetchOptions.ordering || options.ordering,
        };

        const response = await documentService.getDocuments(params);

        setDocuments(response.results);
        setPagination({
          current: params.page,
          pageSize: params.page_size,
          total: response.count,
          hasNext: !!response.next,
          hasPrevious: !!response.previous,
        });
      } catch (err: any) {
        setError(err.message || '获取文档列表失败');
        setDocuments([]);
      } finally {
        setLoading(false);
      }
    },
    [pagination.current, pagination.pageSize, options],
  );

  // 上传文档
  const uploadDocument = useCallback(
    async (
      data: DocumentUpload,
      onProgress?: (progress: number) => void,
    ): Promise<Document> => {
      try {
        setError(null);
        const document = await documentService.uploadDocument(data, onProgress);
        
        // 上传成功后刷新列表
        await fetchDocuments();
        
        return document;
      } catch (err: any) {
        setError(err.message || '上传文档失败');
        throw err;
      }
    },
    [fetchDocuments],
  );

  // 更新文档
  const updateDocument = useCallback(
    async (id: number, data: Partial<Document>): Promise<Document> => {
      try {
        setError(null);
        const updatedDocument = await documentService.updateDocument(id, data);
        
        // 更新本地状态
        setDocuments((prev) =>
          prev.map((doc) => (doc.id === id ? updatedDocument : doc)),
        );
        
        return updatedDocument;
      } catch (err: any) {
        setError(err.message || '更新文档失败');
        throw err;
      }
    },
    [],
  );

  // 删除文档
  const deleteDocument = useCallback(
    async (id: number): Promise<void> => {
      try {
        setError(null);
        await documentService.deleteDocument(id);
        
        // 从本地状态中移除
        setDocuments((prev) => prev.filter((doc) => doc.id !== id));
        
        // 更新分页信息
        setPagination((prev) => ({
          ...prev,
          total: prev.total - 1,
        }));
      } catch (err: any) {
        setError(err.message || '删除文档失败');
        throw err;
      }
    },
    [],
  );

  // 搜索文档
  const searchDocuments = useCallback(
    async (request: SearchRequest): Promise<SearchResponse> => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await documentService.searchDocuments(request);
        
        // 更新文档列表为搜索结果
        setDocuments(response.results.map(result => ({
          id: result.id,
          title: result.title,
          description: result.description,
          file_name: result.file_name,
          file_type: result.file_type,
          category: result.category,
          tags: result.tags,
          uploaded_by: result.uploaded_by,
          created_at: result.created_at,
          // 其他必需字段的默认值
          file: '',
          file_size: 0,
          file_hash: '',
          updated_at: result.created_at,
          is_public: true,
          download_count: 0,
          view_count: 0,
          status: 'completed' as const,
        })));
        
        setPagination({
          current: request.page || 1,
          pageSize: request.page_size || 20,
          total: response.count,
          hasNext: !!response.next,
          hasPrevious: !!response.previous,
        });
        
        return response;
      } catch (err: any) {
        setError(err.message || '搜索文档失败');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  // 刷新文档列表
  const refreshDocuments = useCallback(async () => {
    await fetchDocuments();
  }, [fetchDocuments]);

  // 自动获取数据
  useEffect(() => {
    if (options.autoFetch !== false) {
      fetchDocuments();
    }
  }, [
    options.autoFetch,
    options.categoryId,
    options.tags,
    options.search,
    options.ordering,
  ]);

  return {
    documents,
    loading,
    error,
    pagination,
    fetchDocuments,
    uploadDocument,
    updateDocument,
    deleteDocument,
    searchDocuments,
    refreshDocuments,
  };
};

export default useDocuments;