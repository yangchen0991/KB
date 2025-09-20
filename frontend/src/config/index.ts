import { AppConfig } from '@/types';

// 应用配置
export const appConfig: AppConfig = {
  name: process.env.NEXT_PUBLIC_APP_NAME || '智能知识库系统',
  version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
  description:
    process.env.NEXT_PUBLIC_APP_DESCRIPTION || '企业级知识库管理系统',
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  wsUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
  features: {
    ocr: process.env.NEXT_PUBLIC_ENABLE_OCR === 'true',
    aiClassification:
      process.env.NEXT_PUBLIC_ENABLE_AI_CLASSIFICATION === 'true',
    workflow: process.env.NEXT_PUBLIC_ENABLE_WORKFLOW === 'true',
    monitoring: process.env.NEXT_PUBLIC_ENABLE_MONITORING === 'true',
  },
  upload: {
    maxFileSize: parseInt(process.env.NEXT_PUBLIC_MAX_FILE_SIZE || '104857600'), // 100MB
    allowedTypes: (
      process.env.NEXT_PUBLIC_ALLOWED_FILE_TYPES ||
      'pdf,doc,docx,xls,xlsx,ppt,pptx,jpg,jpeg,png,gif'
    ).split(','),
  },
};

// API端点配置
export const apiEndpoints = {
  // 认证相关
  auth: {
    login: '/api/v1/auth/login/',
    register: '/api/v1/auth/register/',
    refresh: '/api/v1/auth/token/refresh/',
    logout: '/api/v1/auth/logout/',
    profile: '/api/v1/auth/profile/',
  },

  // 文档相关
  documents: {
    list: '/api/v1/documents/',
    upload: '/api/v1/documents/',
    detail: (id: number) => `/api/v1/documents/${id}/`,
    download: (id: number) => `/api/v1/documents/${id}/download/`,
    preview: (id: number) => `/api/v1/documents/${id}/preview/`,
    ocr: (id: number) => `/api/v1/documents/${id}/ocr/`,
  },

  // 分类相关
  categories: {
    list: '/api/v1/classification/categories/',
    create: '/api/v1/classification/categories/',
    detail: (id: number) => `/api/v1/classification/categories/${id}/`,
    tree: '/api/v1/classification/categories/tree/',
  },

  // 标签相关
  tags: {
    list: '/api/v1/classification/tags/',
    create: '/api/v1/classification/tags/',
    popular: '/api/v1/classification/tags/popular/',
  },

  // 搜索相关
  search: {
    documents: '/api/v1/search/documents/',
    suggestions: '/api/v1/search/suggestions/',
    history: '/api/v1/search/history/',
    analytics: '/api/v1/search/analytics/',
  },

  // 工作流相关
  workflows: {
    list: '/api/workflows/',
    create: '/api/workflows/',
    detail: (id: number) => `/api/workflows/${id}/`,
    execute: (id: number) => `/api/workflows/${id}/execute/`,
    executions: (id: number) => `/api/workflows/${id}/executions/`,
  },

  // 监控相关
  monitoring: {
    metrics: '/api/monitoring/metrics/',
    health: '/api/v1/monitoring/health/',
    alerts: '/api/v1/monitoring/alerts/',
    dashboards: '/api/monitoring/dashboards/',
    system: '/api/monitoring/system/',
    application: '/api/monitoring/application/',
  },
};

// 路由配置
export const routes = {
  // 公共路由
  home: '/',
  login: '/auth/login',
  register: '/auth/register',

  // 主要功能路由
  dashboard: '/dashboard',
  documents: '/documents',
  documentDetail: (id: number) => `/documents/${id}`,
  documentUpload: '/documents/upload',

  search: '/search',

  categories: '/categories',
  tags: '/tags',

  workflows: '/workflows',
  workflowDetail: (id: number) => `/workflows/${id}`,
  workflowDesigner: '/workflows/designer',

  monitoring: '/monitoring',
  alerts: '/monitoring/alerts',

  // 用户相关路由
  profile: '/profile',
  settings: '/settings',

  // 管理员路由
  admin: '/admin',
  users: '/admin/users',
  system: '/admin/system',
};

// 本地存储键名
export const storageKeys = {
  accessToken: 'kb_access_token',
  refreshToken: 'kb_refresh_token',
  user: 'kb_user',
  theme: 'kb_theme',
  language: 'kb_language',
  preferences: 'kb_preferences',
  searchHistory: 'kb_search_history',
};

// 主题配置
export const themeConfig = {
  light: {
    primaryColor: '#1890ff',
    borderRadius: 6,
    colorBgContainer: '#ffffff',
    colorText: '#000000d9',
    colorTextSecondary: '#00000073',
    colorBorder: '#d9d9d9',
    colorBgLayout: '#f5f5f5',
  },
  dark: {
    primaryColor: '#1890ff',
    borderRadius: 6,
    colorBgContainer: '#141414',
    colorText: '#ffffffd9',
    colorTextSecondary: '#ffffff73',
    colorBorder: '#434343',
    colorBgLayout: '#000000',
  },
};

// 文件类型配置
export const fileTypeConfig = {
  pdf: {
    icon: 'FilePdfOutlined',
    color: '#ff4d4f',
    accept: '.pdf',
    maxSize: 50 * 1024 * 1024, // 50MB
  },
  doc: {
    icon: 'FileWordOutlined',
    color: '#1890ff',
    accept: '.doc,.docx',
    maxSize: 20 * 1024 * 1024, // 20MB
  },
  xls: {
    icon: 'FileExcelOutlined',
    color: '#52c41a',
    accept: '.xls,.xlsx',
    maxSize: 20 * 1024 * 1024, // 20MB
  },
  ppt: {
    icon: 'FilePptOutlined',
    color: '#fa8c16',
    accept: '.ppt,.pptx',
    maxSize: 50 * 1024 * 1024, // 50MB
  },
  image: {
    icon: 'FileImageOutlined',
    color: '#722ed1',
    accept: '.jpg,.jpeg,.png,.gif,.bmp,.tiff',
    maxSize: 10 * 1024 * 1024, // 10MB
  },
  text: {
    icon: 'FileTextOutlined',
    color: '#13c2c2',
    accept: '.txt,.md,.rtf',
    maxSize: 5 * 1024 * 1024, // 5MB
  },
};

// 分页配置
export const paginationConfig = {
  defaultPageSize: 20,
  pageSizeOptions: ['10', '20', '50', '100'],
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number, range: [number, number]) =>
    `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
};

// 表格配置
export const tableConfig = {
  size: 'middle' as const,
  bordered: false,
  showHeader: true,
  scroll: { x: 'max-content' },
  pagination: paginationConfig,
};

// 上传配置
export const uploadConfig = {
  maxCount: 10,
  multiple: true,
  showUploadList: {
    showPreviewIcon: true,
    showRemoveIcon: true,
    showDownloadIcon: false,
  },
  accept: appConfig.upload.allowedTypes.map((type) => `.${type}`).join(','),
};

// 搜索配置
export const searchConfig = {
  debounceTime: 300,
  minQueryLength: 2,
  maxSuggestions: 10,
  highlightTag: 'mark',
  defaultSortBy: 'relevance',
};

// 监控配置
export const monitoringConfig = {
  refreshInterval: 30000, // 30秒
  chartHeight: 300,
  maxDataPoints: 100,
  alertLevels: {
    low: { color: '#52c41a', threshold: 0.7 },
    medium: { color: '#fa8c16', threshold: 0.8 },
    high: { color: '#ff4d4f', threshold: 0.9 },
    critical: { color: '#a8071a', threshold: 0.95 },
  },
};

// 工作流配置
export const workflowConfig = {
  nodeTypes: [
    { type: 'start', label: '开始', color: '#52c41a' },
    { type: 'end', label: '结束', color: '#ff4d4f' },
    { type: 'task', label: '任务', color: '#1890ff' },
    { type: 'condition', label: '条件', color: '#fa8c16' },
    { type: 'approval', label: '审批', color: '#722ed1' },
  ],
  edgeTypes: [
    { type: 'default', label: '默认' },
    { type: 'conditional', label: '条件' },
  ],
};

export default appConfig;
