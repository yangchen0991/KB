// 用户相关类型
export interface User {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  avatar?: string;
  is_active: boolean;
  is_staff: boolean;
  date_joined: string;
  last_login?: string;
  profile?: UserProfile;
}

export interface UserProfile {
  id: number;
  user: number;
  phone?: string;
  department?: string;
  position?: string;
  bio?: string;
  preferences: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// 认证相关类型
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  first_name: string;
  last_name: string;
}

// 文档相关类型
export interface Document {
  id: number;
  title: string;
  description?: string;
  file: string;
  file_name: string;
  file_size: number;
  file_type: string;
  file_hash: string;
  content?: string;
  ocr_content?: string;
  tags: Tag[];
  category?: Category;
  classification_result?: ClassificationResult;
  uploaded_by: User;
  created_at: string;
  updated_at: string;
  is_public: boolean;
  download_count: number;
  view_count: number;
  status: 'processing' | 'completed' | 'failed';
}

export interface DocumentUpload {
  title: string;
  description?: string;
  file: File;
  tags?: string[];
  category_id?: number;
  is_public?: boolean;
}

// 分类相关类型
export interface Category {
  id: number;
  name: string;
  description?: string;
  parent?: number;
  children?: Category[];
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface Tag {
  id: number;
  name: string;
  color?: string;
  document_count: number;
  created_at: string;
}

export interface ClassificationResult {
  id: number;
  document: number;
  predicted_category: Category;
  confidence: number;
  method: 'rule' | 'ml' | 'manual';
  is_correct?: boolean;
  created_at: string;
}

// 搜索相关类型
export interface SearchRequest {
  query: string;
  category_id?: number;
  tags?: string[];
  file_type?: string;
  date_from?: string;
  date_to?: string;
  sort_by?: 'relevance' | 'date' | 'title';
  page?: number;
  page_size?: number;
}

export interface SearchResponse {
  count: number;
  next?: string;
  previous?: string;
  results: SearchResult[];
  aggregations?: SearchAggregations;
}

export interface SearchResult {
  id: number;
  title: string;
  description?: string;
  file_name: string;
  file_type: string;
  category?: Category;
  tags: Tag[];
  uploaded_by: User;
  created_at: string;
  score: number;
  highlights?: Record<string, string[]>;
}

export interface SearchAggregations {
  categories: Array<{ key: string; doc_count: number }>;
  file_types: Array<{ key: string; doc_count: number }>;
  tags: Array<{ key: string; doc_count: number }>;
}

// 工作流相关类型
export interface Workflow {
  id: number;
  name: string;
  description?: string;
  definition: WorkflowDefinition;
  is_active: boolean;
  trigger_type: 'manual' | 'scheduled' | 'event';
  trigger_config?: Record<string, any>;
  created_by: User;
  created_at: string;
  updated_at: string;
  execution_count: number;
  success_rate: number;
}

export interface WorkflowDefinition {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface WorkflowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, any>;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  type?: string;
}

export interface WorkflowExecution {
  id: number;
  workflow: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
  error_message?: string;
  started_at: string;
  completed_at?: string;
  duration?: number;
}

// 监控相关类型
export interface SystemMetrics {
  id: number;
  timestamp: string;
  cpu_usage_percent: number;
  memory_usage_percent: number;
  disk_usage_percent: number;
  network_io_bytes: number;
  request_count: number;
  error_count: number;
  response_time_avg: number;
}

export interface ApplicationMetrics {
  id: number;
  timestamp: string;
  active_users: number;
  total_users: number;
  total_documents: number;
  documents_uploaded_today: number;
  search_requests_today: number;
  avg_search_response_time: number;
  workflow_executions_today: number;
  workflow_success_rate: number;
}

export interface AlertRule {
  id: number;
  name: string;
  description?: string;
  metric_name: string;
  operator: 'gt' | 'lt' | 'eq' | 'gte' | 'lte';
  threshold: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'active' | 'inactive';
  notification_channels: string[];
  created_by: User;
  created_at: string;
  updated_at: string;
}

export interface AlertInstance {
  id: number;
  alert_rule: AlertRule;
  status: 'firing' | 'resolved' | 'silenced';
  value: number;
  message: string;
  started_at: string;
  resolved_at?: string;
  acknowledged_by?: User;
  acknowledged_at?: string;
}

// API响应类型
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T = any> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}

// 表单相关类型
export interface FormField {
  name: string;
  label: string;
  type:
    | 'text'
    | 'email'
    | 'password'
    | 'textarea'
    | 'select'
    | 'file'
    | 'checkbox';
  required?: boolean;
  placeholder?: string;
  options?: Array<{ label: string; value: any }>;
  validation?: Record<string, any>;
}

// 通用类型
export interface SelectOption {
  label: string;
  value: any;
  disabled?: boolean;
}

export interface TableColumn {
  key: string;
  title: string;
  dataIndex?: string;
  width?: number;
  fixed?: 'left' | 'right';
  sorter?: boolean;
  render?: (value: any, record: any, index: number) => React.ReactNode;
}

export interface MenuItem {
  key: string;
  label: string;
  icon?: React.ReactNode;
  path?: string;
  children?: MenuItem[];
  permission?: string;
}

// 主题相关类型
export interface ThemeConfig {
  primaryColor: string;
  borderRadius: number;
  colorBgContainer: string;
  colorText: string;
  colorTextSecondary: string;
  colorBorder: string;
  colorBgLayout: string;
}

// 配置相关类型
export interface AppConfig {
  name: string;
  version: string;
  description: string;
  apiUrl: string;
  wsUrl: string;
  features: {
    ocr: boolean;
    aiClassification: boolean;
    workflow: boolean;
    monitoring: boolean;
  };
  upload: {
    maxFileSize: number;
    allowedTypes: string[];
  };
}

// 错误类型
export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, any>;
}

export interface ValidationError {
  field: string;
  message: string;
}
