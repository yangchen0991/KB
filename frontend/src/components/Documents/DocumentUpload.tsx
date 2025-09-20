import React, { useState } from 'react';
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
} from 'antd';
import {
  InboxOutlined,
  UploadOutlined,
  DeleteOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { UploadFile, UploadProps } from 'antd/es/upload';
import { useRouter } from 'next/router';
import { useDocuments } from '@/hooks/useDocuments';
import { DocumentUpload as DocumentUploadType } from '@/types';
import { formatFileSize, getFileType } from '@/utils';
import { routes, uploadConfig } from '@/config';

const { Dragger } = Upload;
const { TextArea } = Input;
const { Option } = Select;

interface DocumentUploadProps {
  onSuccess?: (document: any) => void;
  onCancel?: () => void;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({
  onSuccess,
  onCancel,
}) => {
  const [form] = Form.useForm();
  const router = useRouter();
  const { uploadDocument } = useDocuments({ autoFetch: false });

  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>(
    {},
  );

  // 文件上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,
    fileList,
    beforeUpload: (file) => {
      // 检查文件类型
      const fileType = getFileType(file.name);
      const allowedTypes = ['pdf', 'doc', 'xls', 'ppt', 'image', 'text'];

      if (!allowedTypes.includes(fileType)) {
        message.error(`不支持的文件类型: ${file.name}`);
        return false;
      }

      // 检查文件大小
      const maxSize = 100 * 1024 * 1024; // 100MB
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

    try {
      const uploadPromises = fileList.map(async (fileItem) => {
        const file = fileItem.originFileObj as File;

        const uploadData: DocumentUploadType = {
          title: values.title || file.name,
          description: values.description,
          file,
          tags: values.tags,
          category_id: values.category_id,
          is_public: values.is_public || false,
        };

        return uploadDocument(uploadData, (progress) => {
          setUploadProgress((prev) => ({
            ...prev,
            [fileItem.uid]: progress,
          }));
        });
      });

      const results = await Promise.all(uploadPromises);

      message.success(`成功上传 ${results.length} 个文件`);

      if (onSuccess) {
        onSuccess(results);
      } else {
        router.push(routes.documents);
      }
    } catch (error: any) {
      message.error(error.message || '上传失败');
    } finally {
      setUploading(false);
      setUploadProgress({});
    }
  };

  // 获取文件图标
  const getFileIcon = (fileName: string) => {
    const fileType = getFileType(fileName);
    const colorMap = {
      pdf: '#ff4d4f',
      doc: '#1890ff',
      xls: '#52c41a',
      ppt: '#fa8c16',
      image: '#722ed1',
      text: '#13c2c2',
    };

    return (
      <FileTextOutlined
        style={{ color: colorMap[fileType as keyof typeof colorMap] || '#666' }}
      />
    );
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card title="上传文档" className="shadow-sm">
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            is_public: false,
          }}
        >
          {/* 文件上传区域 */}
          <Form.Item
            label="选择文件"
            required
            help="支持 PDF、Word、Excel、PowerPoint、图片等格式，单个文件最大 100MB"
          >
            <Dragger
              {...uploadProps}
              className="border-dashed border-2 border-gray-300 hover:border-blue-400"
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined className="text-4xl text-blue-500" />
              </p>
              <p className="ant-upload-text text-lg font-medium">
                点击或拖拽文件到此区域上传
              </p>
              <p className="ant-upload-hint text-gray-500">
                支持单个或批量上传，严禁上传公司数据或其他敏感信息
              </p>
            </Dragger>
          </Form.Item>

          {/* 文件列表 */}
          {fileList.length > 0 && (
            <Card size="small" title="待上传文件" className="mb-4">
              <div className="space-y-2">
                {fileList.map((file) => (
                  <div
                    key={file.uid}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center space-x-3 flex-1">
                      <div className="text-lg">{getFileIcon(file.name)}</div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">{file.name}</div>
                        <div className="text-sm text-gray-500">
                          {formatFileSize(file.size || 0)}
                        </div>
                        {uploadProgress[file.uid] !== undefined && (
                          <Progress
                            percent={uploadProgress[file.uid]}
                            size="small"
                            className="mt-1"
                          />
                        )}
                      </div>
                    </div>
                    <Button
                      type="text"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => {
                        setFileList((prev) =>
                          prev.filter((item) => item.uid !== file.uid),
                        );
                      }}
                      disabled={uploading}
                    />
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* 文档信息 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Form.Item
              name="title"
              label="文档标题"
              rules={[
                { required: true, message: '请输入文档标题' },
                { max: 200, message: '标题不能超过200个字符' },
              ]}
            >
              <Input placeholder="请输入文档标题" />
            </Form.Item>

            <Form.Item name="category_id" label="文档分类">
              <Select placeholder="选择文档分类" allowClear>
                <Option value={1}>技术文档</Option>
                <Option value={2}>产品文档</Option>
                <Option value={3}>管理文档</Option>
                <Option value={4}>培训资料</Option>
              </Select>
            </Form.Item>
          </div>

          <Form.Item name="description" label="文档描述">
            <TextArea
              rows={3}
              placeholder="请输入文档描述（可选）"
              maxLength={500}
              showCount
            />
          </Form.Item>

          <Form.Item name="tags" label="标签" help="输入标签名称，按回车添加">
            <Select
              mode="tags"
              placeholder="添加标签"
              style={{ width: '100%' }}
              tokenSeparators={[',']}
            >
              <Option value="重要">重要</Option>
              <Option value="紧急">紧急</Option>
              <Option value="草稿">草稿</Option>
              <Option value="已审核">已审核</Option>
            </Select>
          </Form.Item>

          <Form.Item name="is_public" label="公开设置" valuePropName="checked">
            <Switch checkedChildren="公开" unCheckedChildren="私有" />
          </Form.Item>

          {/* 操作按钮 */}
          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={uploading}
                icon={<UploadOutlined />}
                size="large"
                disabled={fileList.length === 0}
              >
                {uploading ? '上传中...' : '开始上传'}
              </Button>
              <Button
                size="large"
                onClick={() => {
                  if (onCancel) {
                    onCancel();
                  } else {
                    router.back();
                  }
                }}
                disabled={uploading}
              >
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {/* 上传提示 */}
      <Alert
        message="上传提示"
        description={
          <div className="space-y-2">
            <div>• 支持的文件格式：PDF、Word、Excel、PowerPoint、图片等</div>
            <div>• 单个文件大小限制：100MB</div>
            <div>• 上传后系统会自动进行OCR文字识别和智能分类</div>
            <div>• 请确保上传的文件不包含敏感信息</div>
          </div>
        }
        type="info"
        showIcon
      />
    </div>
  );
};

export default DocumentUpload;
