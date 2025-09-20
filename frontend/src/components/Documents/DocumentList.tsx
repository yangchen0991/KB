import React, { useState, useEffect } from 'react';
import {
  Table,
  Card,
  Button,
  Input,
  Select,
  Tag,
  Space,
  Tooltip,
  Modal,
  message,
  Upload,
  Dropdown,
  Typography,
} from 'antd';
import {
  SearchOutlined,
  UploadOutlined,
  DownloadOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  MoreOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FileExcelOutlined,
  FilePptOutlined,
  FileImageOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useDocuments } from '@/hooks/useDocuments';
import { Document } from '@/types';
import { formatFileSize, formatDate } from '@/utils';

const { Search } = Input;
const { Option } = Select;
const { Text } = Typography;

interface DocumentListProps {
  categoryId?: number;
  showUpload?: boolean;
  onDocumentSelect?: (document: Document) => void;
}

const DocumentList: React.FC<DocumentListProps> = ({
  categoryId,
  showUpload = true,
  onDocumentSelect,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewDocument, setPreviewDocument] = useState<Document | null>(null);

  const {
    documents,
    loading,
    error,
    pagination,
    fetchDocuments,
    deleteDocument,
    refreshDocuments,
  } = useDocuments({
    categoryId,
    search: searchQuery,
    autoFetch: true,
  });

  // 文件类型图标映射
  const getFileIcon = (fileType: string) => {
    const type = fileType.toLowerCase();
    if (type.includes('pdf')) return <FilePdfOutlined style={{ color: '#ff4d4f' }} />;
    if (type.includes('word') || type.includes('doc')) return <FileWordOutlined style={{ color: '#1890ff' }} />;
    if (type.includes('excel') || type.includes('sheet')) return <FileExcelOutlined style={{ color: '#52c41a' }} />;
    if (type.includes('powerpoint') || type.includes('presentation')) return <FilePptOutlined style={{ color: '#fa8c16' }} />;
    if (type.includes('image')) return <FileImageOutlined style={{ color: '#722ed1' }} />;
    return <FileTextOutlined style={{ color: '#13c2c2' }} />;
  };

  // 表格列定义
  const columns: ColumnsType<Document> = [
    {
      title: '文档名称',
      dataIndex: 'title',
      key: 'title',
      width: 300,
      render: (title: string, record: Document) => (
        <Space>
          {getFileIcon(record.file_type)}
          <div>
            <div className="font-medium text-gray-900">{title}</div>
            <div className="text-sm text-gray-500">{record.file_name}</div>
          </div>
        </Space>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: (category) => (
        category ? (
          <Tag color="blue">{category.name}</Tag>
        ) : (
          <Text type="secondary">未分类</Text>
        )
      ),
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      width: 200,
      render: (tags: any[]) => (
        <Space wrap>
          {tags?.slice(0, 3).map((tag) => (
            <Tag key={tag.id} color={tag.color || 'default'}>
              {tag.name}
            </Tag>
          ))}
          {tags?.length > 3 && (
            <Tag>+{tags.length - 3}</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '上传者',
      dataIndex: 'uploaded_by',
      key: 'uploaded_by',
      width: 120,
      render: (user) => user?.username || '未知',
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) => formatDate(date),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const statusConfig = {
          processing: { color: 'processing', text: '处理中' },
          completed: { color: 'success', text: '已完成' },
          failed: { color: 'error', text: '失败' },
        };
        const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.completed;
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      fixed: 'right',
      render: (_, record: Document) => (
        <Space>
          <Tooltip title="预览">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handlePreview(record)}
            />
          </Tooltip>
          <Tooltip title="下载">
            <Button
              type="text"
              icon={<DownloadOutlined />}
              onClick={() => handleDownload(record)}
            />
          </Tooltip>
          <Dropdown
            menu={{
              items: [
                {
                  key: 'edit',
                  label: '编辑',
                  icon: <EditOutlined />,
                  onClick: () => handleEdit(record),
                },
                {
                  key: 'delete',
                  label: '删除',
                  icon: <DeleteOutlined />,
                  danger: true,
                  onClick: () => handleDelete(record),
                },
              ],
            }}
          >
            <Button type="text" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      ),
    },
  ];

  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchQuery(value);
  };

  // 处理预览
  const handlePreview = (document: Document) => {
    setPreviewDocument(document);
    setPreviewVisible(true);
  };

  // 处理下载
  const handleDownload = async (document: Document) => {
    try {
      // 这里应该调用下载API
      message.success(`开始下载 ${document.title}`);
    } catch (error) {
      message.error('下载失败');
    }
  };

  // 处理编辑
  const handleEdit = (document: Document) => {
    if (onDocumentSelect) {
      onDocumentSelect(document);
    }
  };

  // 处理删除
  const handleDelete = (document: Document) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除文档 "${document.title}" 吗？此操作不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await deleteDocument(document.id);
          message.success('删除成功');
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  // 批量删除
  const handleBatchDelete = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要删除的文档');
      return;
    }

    Modal.confirm({
      title: '批量删除',
      content: `确定要删除选中的 ${selectedRowKeys.length} 个文档吗？此操作不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          // 这里应该调用批量删除API
          message.success(`成功删除 ${selectedRowKeys.length} 个文档`);
          setSelectedRowKeys([]);
          refreshDocuments();
        } catch (error) {
          message.error('批量删除失败');
        }
      },
    });
  };

  // 表格行选择配置
  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => {
      setSelectedRowKeys(keys);
    },
  };

  // 分页配置
  const paginationConfig = {
    current: pagination.current,
    pageSize: pagination.pageSize,
    total: pagination.total,
    showSizeChanger: true,
    showQuickJumper: true,
    showTotal: (total: number, range: [number, number]) =>
      `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
    onChange: (page: number, pageSize: number) => {
      fetchDocuments({ page, pageSize });
    },
  };

  return (
    <div className="space-y-4">
      {/* 工具栏 */}
      <Card>
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <Search
              placeholder="搜索文档..."
              allowClear
              enterButton={<SearchOutlined />}
              size="large"
              style={{ width: 300 }}
              onSearch={handleSearch}
            />
            <Select
              placeholder="选择分类"
              allowClear
              style={{ width: 150 }}
              onChange={(value) => {
                // 这里应该更新分类筛选
              }}
            >
              <Option value="1">技术文档</Option>
              <Option value="2">产品文档</Option>
              <Option value="3">管理文档</Option>
            </Select>
          </div>
          <div className="flex items-center space-x-2">
            {selectedRowKeys.length > 0 && (
              <Button
                danger
                onClick={handleBatchDelete}
              >
                批量删除 ({selectedRowKeys.length})
              </Button>
            )}
            {showUpload && (
              <Button
                type="primary"
                icon={<UploadOutlined />}
                onClick={() => {
                  // 这里应该打开上传对话框
                }}
              >
                上传文档
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* 文档列表 */}
      <Card>
        <Table
          columns={columns}
          dataSource={documents}
          rowKey="id"
          loading={loading}
          pagination={paginationConfig}
          rowSelection={rowSelection}
          scroll={{ x: 1200 }}
          size="middle"
        />
      </Card>

      {/* 预览模态框 */}
      <Modal
        title={`预览 - ${previewDocument?.title}`}
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={null}
        width={800}
        style={{ top: 20 }}
      >
        {previewDocument && (
          <div className="text-center">
            <p className="text-gray-500 mb-4">
              文档预览功能正在开发中...
            </p>
            <div className="text-left space-y-2">
              <p><strong>文件名:</strong> {previewDocument.file_name}</p>
              <p><strong>文件大小:</strong> {formatFileSize(previewDocument.file_size)}</p>
              <p><strong>文件类型:</strong> {previewDocument.file_type}</p>
              <p><strong>上传时间:</strong> {formatDate(previewDocument.created_at)}</p>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default DocumentList;