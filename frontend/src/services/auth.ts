import { apiService } from './api';
import { apiEndpoints, storageKeys } from '@/config';
import { LoginRequest, LoginResponse, RegisterRequest, User } from '@/types';

export class AuthService {
  // 登录
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await apiService.post<LoginResponse>(
      apiEndpoints.auth.login,
      credentials,
    );

    // 保存token和用户信息
    if (response.access) {
      localStorage.setItem(storageKeys.accessToken, response.access);
      localStorage.setItem(storageKeys.refreshToken, response.refresh);
      localStorage.setItem(storageKeys.user, JSON.stringify(response.user));
    }

    return response;
  }

  // 注册
  async register(userData: RegisterRequest): Promise<User> {
    return await apiService.post<User>(apiEndpoints.auth.register, userData);
  }

  // 登出
  async logout(): Promise<void> {
    try {
      const refreshToken = localStorage.getItem(storageKeys.refreshToken);
      if (refreshToken) {
        await apiService.post(apiEndpoints.auth.logout, {
          refresh: refreshToken,
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // 清除本地存储
      this.clearLocalStorage();
    }
  }

  // 刷新token
  async refreshToken(): Promise<string> {
    const refreshToken = localStorage.getItem(storageKeys.refreshToken);
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await apiService.post<{ access: string }>(
      apiEndpoints.auth.refresh,
      { refresh: refreshToken },
    );

    localStorage.setItem(storageKeys.accessToken, response.access);
    return response.access;
  }

  // 获取当前用户信息
  async getCurrentUser(): Promise<User> {
    return await apiService.get<User>(apiEndpoints.auth.profile);
  }

  // 更新用户信息
  async updateProfile(userData: Partial<User>): Promise<User> {
    const response = await apiService.patch<User>(
      apiEndpoints.auth.profile,
      userData,
    );

    // 更新本地存储的用户信息
    localStorage.setItem(storageKeys.user, JSON.stringify(response));
    return response;
  }

  // 修改密码
  async changePassword(data: {
    old_password: string;
    new_password: string;
  }): Promise<void> {
    await apiService.post('/api/v1/auth/password/change/', data);
  }

  // 重置密码
  async resetPassword(email: string): Promise<void> {
    await apiService.post('/api/v1/auth/reset-password/', { email });
  }

  // 确认重置密码
  async confirmResetPassword(data: {
    token: string;
    new_password: string;
  }): Promise<void> {
    await apiService.post('/api/v1/auth/reset-password/confirm/', data);
  }

  // 检查是否已登录
  isAuthenticated(): boolean {
    const token = localStorage.getItem(storageKeys.accessToken);
    const user = localStorage.getItem(storageKeys.user);
    return !!(token && user);
  }

  // 获取本地存储的用户信息
  getLocalUser(): User | null {
    try {
      const userStr = localStorage.getItem(storageKeys.user);
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      console.error('Error parsing user from localStorage:', error);
      return null;
    }
  }

  // 获取访问token
  getAccessToken(): string | null {
    return localStorage.getItem(storageKeys.accessToken);
  }

  // 获取刷新token
  getRefreshToken(): string | null {
    return localStorage.getItem(storageKeys.refreshToken);
  }

  // 清除本地存储
  clearLocalStorage(): void {
    localStorage.removeItem(storageKeys.accessToken);
    localStorage.removeItem(storageKeys.refreshToken);
    localStorage.removeItem(storageKeys.user);
  }

  // 检查token是否即将过期
  isTokenExpiringSoon(): boolean {
    const token = this.getAccessToken();
    if (!token) return true;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload.exp * 1000; // 转换为毫秒
      const now = Date.now();
      const fiveMinutes = 5 * 60 * 1000;

      return exp - now < fiveMinutes;
    } catch (error) {
      console.error('Error parsing token:', error);
      return true;
    }
  }

  // 自动刷新token
  async autoRefreshToken(): Promise<void> {
    if (this.isTokenExpiringSoon()) {
      try {
        await this.refreshToken();
      } catch (error) {
        console.error('Auto refresh token failed:', error);
        this.clearLocalStorage();
        if (typeof window !== 'undefined') {
          window.location.href = '/auth/login';
        }
      }
    }
  }

  // 验证邮箱
  async verifyEmail(token: string): Promise<void> {
    await apiService.post('/api/accounts/verify-email/', { token });
  }

  // 重发验证邮件
  async resendVerificationEmail(): Promise<void> {
    await apiService.post('/api/accounts/resend-verification/');
  }

  // 检查用户名是否可用
  async checkUsernameAvailability(username: string): Promise<boolean> {
    try {
      await apiService.post('/api/accounts/check-username/', { username });
      return true;
    } catch (error) {
      return false;
    }
  }

  // 检查邮箱是否可用
  async checkEmailAvailability(email: string): Promise<boolean> {
    try {
      await apiService.post('/api/accounts/check-email/', { email });
      return true;
    } catch (error) {
      return false;
    }
  }

  // 获取用户权限
  async getUserPermissions(): Promise<string[]> {
    const response = await apiService.get<{ permissions: string[] }>(
      '/api/accounts/permissions/',
    );
    return response.permissions;
  }

  // 检查用户是否有特定权限
  hasPermission(permission: string, userPermissions?: string[]): boolean {
    const user = this.getLocalUser();
    if (!user) return false;

    // 管理员拥有所有权限
    if (user.is_staff) return true;

    // 检查具体权限
    if (userPermissions) {
      return userPermissions.includes(permission);
    }

    return false;
  }

  // 启用双因素认证
  async enableTwoFactor(): Promise<{ qr_code: string; secret: string }> {
    return await apiService.post('/api/accounts/2fa/enable/');
  }

  // 确认双因素认证
  async confirmTwoFactor(token: string): Promise<void> {
    await apiService.post('/api/accounts/2fa/confirm/', { token });
  }

  // 禁用双因素认证
  async disableTwoFactor(token: string): Promise<void> {
    await apiService.post('/api/accounts/2fa/disable/', { token });
  }

  // 双因素认证登录
  async loginWithTwoFactor(data: {
    email: string;
    password: string;
    token: string;
  }): Promise<LoginResponse> {
    const response = await apiService.post<LoginResponse>(
      '/api/accounts/2fa/login/',
      data,
    );

    if (response.access) {
      localStorage.setItem(storageKeys.accessToken, response.access);
      localStorage.setItem(storageKeys.refreshToken, response.refresh);
      localStorage.setItem(storageKeys.user, JSON.stringify(response.user));
    }

    return response;
  }
}

// 创建认证服务实例
export const authService = new AuthService();

// 认证状态管理
export class AuthStateManager {
  private listeners: Array<
    (isAuthenticated: boolean, user: User | null) => void
  > = [];

  // 添加状态监听器
  addListener(
    listener: (isAuthenticated: boolean, user: User | null) => void,
  ): void {
    this.listeners.push(listener);
  }

  // 移除状态监听器
  removeListener(
    listener: (isAuthenticated: boolean, user: User | null) => void,
  ): void {
    const index = this.listeners.indexOf(listener);
    if (index > -1) {
      this.listeners.splice(index, 1);
    }
  }

  // 通知状态变化
  notifyStateChange(): void {
    const isAuthenticated = authService.isAuthenticated();
    const user = authService.getLocalUser();

    this.listeners.forEach((listener) => {
      try {
        listener(isAuthenticated, user);
      } catch (error) {
        console.error('Error in auth state listener:', error);
      }
    });
  }

  // 初始化状态管理
  initialize(): void {
    // 监听localStorage变化
    if (typeof window !== 'undefined') {
      window.addEventListener('storage', (event) => {
        if (
          event.key === storageKeys.accessToken ||
          event.key === storageKeys.user
        ) {
          this.notifyStateChange();
        }
      });

      // 定期检查token状态
      setInterval(() => {
        if (authService.isAuthenticated()) {
          authService.autoRefreshToken();
        }
      }, 60000); // 每分钟检查一次
    }
  }
}

export const authStateManager = new AuthStateManager();

export default authService;
