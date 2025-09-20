import React, { useState, useEffect } from 'react';
import {
  Upload,
  Button,
  Form,
  Input,
  Select,
  Switch,
  Card,
  Progress,
  message,
  Space,
  Tag,
  Alert,
  Row,
  Col,
  Typography,
  Divider,
} from 'antd';
import {
  InboxOutlined,
  UploadOutlined,
  DeleteOutlined,
  FileTextOutlined,
  EyeOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import { UploadFile, UploadProps } from 'antd/es/upload';
import { useRouter } from 'next/router';
import { documentsService } from '@/services/documents';
import { formatFileSize, getFileType } from '@/utils';
import MainLayout from '@/components/Layout/MainLayout';

const { Dragger } = Upload;
const { TextArea } = Input;
const { Option } = Select;
const { Title, Text } = Typography;

interface Category {
  id: string;
  name: string;
  description: string;
  color: string;
  document_count: number;
}

interface TagItem {
  id: string;
  name: string;
  color: string;
  document_count: number;
}

const DocumentUploadPage: React.FC = () => {
  const [form] = Form.useForm();
  const router = useRouter();

  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [categories, setCategories] = useState<Category[]>([]);
  const [tags, setTags] = useState<TagItem[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [uploadedDocuments, setUploadedDocuments] = useState<any[]>([]);

  // 加载分类和标签
  useEffect(() => {
    loadCategoriesAndTags();
  }, []);

  const loadCategoriesAndTags = async () => {
    try {
      const [categoriesRes, tagsRes] = await Promise.all([
        documentsService.getCategories(),
        documentsService.getTags(),
      ]);
      
      setCategories(categoriesRes.categories);
      setTags(tagsRes.tags);
    } catch (error) {
      console.error('加载分类和标签失败:', error);
      message.error('加载分类和标签失败');
    }
  };

  // 文件上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,
    fileList,
    beforeUpload: (file) => {
      // 检查文件类型
      const fileType = getFileType(file.name);
      const allowedTypes = ['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'tiff'];

      if (!allowedTypes.includes(fileType)) {
        message.error(`不支持的文件类型: ${file.name}`);
        return false;
      }

      // 检查文件大小
      const maxSize = 50 * 1024 * 1024; // 50MB
      if (file.size > maxSize) {
        message.error(`文件大小不能超过 ${formatFileSize(maxSize)}`);
        return false;
      }

      return false; // 阻止自动上传
    },
    onChange: (info) => {
      setFileList(info.fileList);
    },
    onRemove: (file) => {
      setFileList((prev) => prev.filter((item) => item.uid !== file.uid));
    },
  };

  // 处理表单提交
  const handleSubmit = async (values: any) => {
    if (fileList.length === 0) {
      message.error('请选择要上传的文件');
      return;
    }

    setUploading(true);
    const results: any[] = [];

    try {
      for (const fileItem of fileList) {
        const file = fileItem.originFileObj as File;

        const uploadData = {
          title: values.title || file.name,
          description: values.description,
          file,
          category: values.category,
          tags: selectedTags,
          is_public: values.is_public || false,
          onProgress: (progressEvent: any) => {
            const progress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setUploadProgress((prev) => ({
              ...prev,
              [file.name]: progress,
            }));
          },
        };

        const result = await documentsService.uploadDocument(uploadData);
        results.push(result);
        
        message.success(`${file.name} 上传成功`);
      }

      setUploadedDocuments(results);
      
      // 重置表单
      form.resetFields();
      setFileList([]);
      setSelectedTags([]);
      setUploadProgress({});
      
      message.success(`成功上传 ${results.length} 个文件`);

    } catch (error: any) {
      console.error('上传失败:', error);
      message.error(error.response?.data?.message || '上传失败');
    } finally {
      setUploading(false);
    }
  };

  // 预览文档
  const handlePreview = async (documentId: string) => {
    try {
      const preview = await documentsService.previewDocument(documentId);
      // 这里可以打开预览模态框
      message.info('预览功能开发中');
    } catch (error) {
      message.error('预览失败');
    }
  };

  // 下载文档
  const handleDownload = async (documentId: string, title: string) => {
    try {
      const blob = await documentsService.downloadDocument(documentId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = title;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      message.error('下载失败');
    }
  };

  return (
    <MainLayout>
      <div style={{ padding: '24px' }}>
        <Title level={2}>文档上传</Title>
        
        <Row gutter={24}>
          <Col span={16}>
            <Card title="上传文档" style={{ marginBottom: 24 }}>
              <Form
                form={form}
                layout="vertical"
                onFinish={handleSubmit}
              >
                <Form.Item
                  name="title"
                  label="文档标题"
                  rules={[{ required: true, message: '请输入文档标题' }]}
                >
                  <Input placeholder="请输入文档标题" />
                </Form.Item>

                <Form.Item
                  name="description"
                  label="文档描述"
                >
                  <TextArea
                    rows={3}
                    placeholder="请输入文档描述（可选）"
                  />
                </Form.Item>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="category"
                      label="文档分类"
                    >
                      <Select placeholder="请选择分类（可选）" allowClear>
                        {categories.map((category) => (
                          <Option key={category.id} value={category.id}>
                            <Space>
                              <div
                                style={{
                                  width: 12,
                                  height: 12,
                                  backgroundColor: category.color,
                                  borderRadius: 2,
                                }}
                              />
                              {category.name}
                            </Space>
                          </Option>
                        ))}
                      </Select>
                    </Form.Item>
                  </Col>
                  
                  <Col span={12}>
                    <Form.Item
                      name="is_public"
                      label="公开文档"
                      valuePropName="checked"
                    >
                      <Switch />
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item label="文档标签">
                  <Select
                    mode="multiple"
                    placeholder="请选择标签（可选）"
                    value={selectedTags}
                    onChange={setSelectedTags}
                    style={{ width: '100%' }}
                  >
                    {tags.map((tag) => (
                      <Option key={tag.id} value={tag.id}>
                        <Tag color={tag.color}>{tag.name}</Tag>
                      </Option>
                    ))}
                  </Select>
                </Form.Item>

                <Form.Item label="选择文件">
                  <Dragger {...uploadProps} style={{ marginBottom: 16 }}>
                    <p className="ant-upload-drag-icon">
                      <InboxOutlined />
                    </p>
                    <p className="ant-upload-text">
                      点击或拖拽文件到此区域上传
                    </p>
                    <p className="ant-upload-hint">
                      支持 PDF、DOC、DOCX、TXT、JPG、PNG 等格式，单个文件不超过 50MB
                    </p>
                  </Dragger>
                </Form.Item>

                {/* 上传进度 */}
                {Object.keys(uploadProgress).length > 0 && (
                  <div style={{ marginBottom: 16 }}>
                    {Object.entries(uploadProgress).map(([fileName, progress]) => (
                      <div key={fileName} style={{ marginBottom: 8 }}>
                        <Text>{fileName}</Text>
                        <Progress percent={progress} size="small" />
                      </div>
                    ))}
                  </div>
                )}

                <Form.Item>
                  <Space>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={uploading}
                      icon={<UploadOutlined />}
                      disabled={fileList.length === 0}
                    >
                      {uploading ? '上传中...' : '开始上传'}
                    </Button>
                    
                    <Button
                      onClick={() => {
                        form.resetFields();
                        setFileList([]);
                        setSelectedTags([]);
                      }}
                    >
                      重置
                    </Button>
                  </Space>
                </Form.Item>
              </Form>
            </Card>
          </Col>

          <Col span={8}>
            <Card title="上传说明" style={{ marginBottom: 24 }}>
              <Alert
                message="支持的文件格式"
                description={
                  <ul style={{ margin: 0, paddingLeft: 20 }}>
                    <li>文档：PDF, DOC, DOCX, TXT</li>
                    <li>图片：JPG, PNG, TIFF</li>
                    <li>单个文件大小限制：50MB</li>
                  </ul>
                }
                type="info"
                showIcon
              />
              
              <Divider />
              
              <div>
                <Title level={5}>功能特性</Title>
                <ul style={{ paddingLeft: 20 }}>
                  <li>自动OCR文字识别</li>
                  <li>智能分类建议</li>
                  <li>全文搜索支持</li>
                  <li>多格式预览</li>
                  <li>权限控制</li>
                </ul>
              </div>
            </Card>

            {/* 分类统计 */}
            <Card title="分类统计" size="small">
              <div style={{ maxHeight: 200, overflowY: 'auto' }}>
                {categories.map((category) => (
                  <div
                    key={category.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '4px 0',
                    }}
                  >
                    <Space>
                      <div
                        style={{
                          width: 8,
                          height: 8,
                          backgroundColor: category.color,
                          borderRadius: '50%',
                        }}
                      />
                      <Text>{category.name}</Text>
                    </Space>
                    <Text type="secondary">{category.document_count}</Text>
                  </div>
                ))}
              </div>
            </Card>
          </Col>
        </Row>

        {/* 已上传文档列表 */}
        {uploadedDocuments.length > 0 && (
          <Card title="上传成功的文档" style={{ marginTop: 24 }}>
            <div style={{ display: 'grid', gap: 16 }}>
              {uploadedDocuments.map((doc) => (
                <Card
                  key={doc.id}
                  size="small"
                  actions={[
                    <Button
                      key="preview"
                      type="link"
                      icon={<EyeOutlined />}
                      onClick={() => handlePreview(doc.id)}
                    >
                      预览
                    </Button>,
                    <Button
                      key="download"
                      type="link"
                      icon={<DownloadOutlined />}
                      onClick={() => handleDownload(doc.id, doc.title)}
                    >
                      下载
                    </Button>,
                  ]}
                >
                  <Card.Meta
                    avatar={<FileTextOutlined style={{ fontSize: 24 }} />}
                    title={doc.title}
                    description={
                      <div>
                        <Text type="secondary">{doc.description}</Text>
                        <br />
                        <Text type="secondary">
                          {formatFileSize(doc.file_size)} • {doc.file_type.toUpperCase()}
                        </Text>
                      </div>
                    }
                  />
                </Card>
              ))}
            </div>
          </Card>
        )}
      </div>
    </MainLayout>
  );
};

export default DocumentUploadPage;