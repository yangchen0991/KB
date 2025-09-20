import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { appConfig, storageKeys } from '@/config';
import { ApiResponse, ApiError } from '@/types';

// 创建axios实例
const createApiInstance = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: appConfig.apiUrl,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // 请求拦截器
  instance.interceptors.request.use(
    (config) => {
      // 添加认证token
      const token = localStorage.getItem(storageKeys.accessToken);
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      // 添加请求ID用于追踪
      config.headers['X-Request-ID'] = generateRequestId();

      // 记录请求日志
      if (process.env.NODE_ENV === 'development') {
        console.log(
          `[API Request] ${config.method?.toUpperCase()} ${config.url}`,
          {
            params: config.params,
            data: config.data,
          },
        );
      }

      return config;
    },
    (error) => {
      console.error('[API Request Error]', error);
      return Promise.reject(error);
    },
  );

  // 响应拦截器
  instance.interceptors.response.use(
    (response: AxiosResponse) => {
      // 记录响应日志
      if (process.env.NODE_ENV === 'development') {
        console.log(
          `[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`,
          {
            status: response.status,
            data: response.data,
          },
        );
      }

      return response;
    },
    async (error) => {
      const originalRequest = error.config;

      // 处理401错误（token过期）
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          const refreshToken = localStorage.getItem(storageKeys.refreshToken);
          if (refreshToken) {
            const response = await axios.post(
              `${appConfig.apiUrl}/api/v1/auth/token/refresh/`,
              {
                refresh: refreshToken,
              },
            );

            const { access } = response.data;
            localStorage.setItem(storageKeys.accessToken, access);

            // 重试原请求
            originalRequest.headers.Authorization = `Bearer ${access}`;
            return instance(originalRequest);
          }
        } catch (refreshError) {
          // 刷新token失败，清除本地存储并跳转到登录页
          localStorage.removeItem(storageKeys.accessToken);
          localStorage.removeItem(storageKeys.refreshToken);
          localStorage.removeItem(storageKeys.user);

          if (typeof window !== 'undefined') {
            window.location.href = '/auth/login';
          }
        }
      }

      // 处理其他错误
      const apiError: ApiError = {
        message: error.response?.data?.message || error.message || '请求失败',
        code: error.response?.data?.code || error.code,
        details: error.response?.data?.details || error.response?.data,
      };

      console.error('[API Response Error]', apiError);
      return Promise.reject(apiError);
    },
  );

  return instance;
};

// 生成请求ID
const generateRequestId = (): string => {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

// API实例
export const api = createApiInstance();

// 通用API方法
export class ApiService {
  private instance: AxiosInstance;

  constructor(instance: AxiosInstance = api) {
    this.instance = instance;
  }

  // GET请求
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.get<T>(url, config);
    return response.data;
  }

  // POST请求
  async post<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig,
  ): Promise<T> {
    const response = await this.instance.post<T>(url, data, config);
    return response.data;
  }

  // PUT请求
  async put<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig,
  ): Promise<T> {
    const response = await this.instance.put<T>(url, data, config);
    return response.data;
  }

  // PATCH请求
  async patch<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig,
  ): Promise<T> {
    const response = await this.instance.patch<T>(url, data, config);
    return response.data;
  }

  // DELETE请求
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.delete<T>(url, config);
    return response.data;
  }

  // 文件上传
  async upload<T = any>(
    url: string,
    file: File,
    data?: Record<string, any>,
    onProgress?: (progress: number) => void,
  ): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    // 添加其他数据
    if (data) {
      Object.keys(data).forEach((key) => {
        const value = data[key];
        if (value !== undefined && value !== null) {
          if (typeof value === 'object') {
            formData.append(key, JSON.stringify(value));
          } else {
            formData.append(key, String(value));
          }
        }
      });
    }

    const config: AxiosRequestConfig = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total,
          );
          onProgress(progress);
        }
      },
    };

    const response = await this.instance.post<T>(url, formData, config);
    return response.data;
  }

  // 文件下载
  async download(url: string, filename?: string): Promise<void> {
    const response = await this.instance.get(url, {
      responseType: 'blob',
    });

    // 创建下载链接
    const blob = new Blob([response.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  // 批量请求
  async batch<T = any>(requests: Array<() => Promise<any>>): Promise<T[]> {
    const results = await Promise.allSettled(
      requests.map((request) => request()),
    );

    return results.map((result, index) => {
      if (result.status === 'fulfilled') {
        return result.value;
      } else {
        console.error(`[Batch Request ${index}] Failed:`, result.reason);
        throw result.reason;
      }
    });
  }

  // 重试请求
  async retry<T = any>(
    request: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000,
  ): Promise<T> {
    let lastError: any;

    for (let i = 0; i <= maxRetries; i++) {
      try {
        return await request();
      } catch (error) {
        lastError = error;

        if (i < maxRetries) {
          await new Promise((resolve) =>
            setTimeout(resolve, delay * Math.pow(2, i)),
          );
        }
      }
    }

    throw lastError;
  }
}

// 默认API服务实例
export const apiService = new ApiService();

// 请求缓存
class RequestCache {
  private cache = new Map<
    string,
    { data: any; timestamp: number; ttl: number }
  >();

  set(key: string, data: any, ttl: number = 5 * 60 * 1000): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    });
  }

  get(key: string): any | null {
    const item = this.cache.get(key);
    if (!item) return null;

    if (Date.now() - item.timestamp > item.ttl) {
      this.cache.delete(key);
      return null;
    }

    return item.data;
  }

  clear(): void {
    this.cache.clear();
  }

  delete(key: string): void {
    this.cache.delete(key);
  }
}

export const requestCache = new RequestCache();

// 带缓存的API请求
export const cachedApiService = {
  async get<T = any>(
    url: string,
    config?: AxiosRequestConfig & { cache?: boolean; ttl?: number },
  ): Promise<T> {
    const cacheKey = `${url}_${JSON.stringify(config?.params || {})}`;

    if (config?.cache !== false) {
      const cached = requestCache.get(cacheKey);
      if (cached) {
        return cached;
      }
    }

    const data = await apiService.get<T>(url, config);

    if (config?.cache !== false) {
      requestCache.set(cacheKey, data, config?.ttl);
    }

    return data;
  },

  clearCache(): void {
    requestCache.clear();
  },

  deleteCache(url: string, params?: any): void {
    const cacheKey = `${url}_${JSON.stringify(params || {})}`;
    requestCache.delete(cacheKey);
  },
};

export default apiService;
