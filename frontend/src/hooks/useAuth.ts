import { useState, useEffect, useCallback } from 'react';
import { authService, authStateManager } from '@/services/auth';
import { User, LoginRequest, RegisterRequest } from '@/types';

interface UseAuthReturn {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
}

export const useAuth = (): UseAuthReturn => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // 初始化认证状态
  const initializeAuth = useCallback(async () => {
    try {
      setIsLoading(true);

      // 检查本地存储的认证状态
      const localUser = authService.getLocalUser();
      const hasToken = authService.isAuthenticated();

      if (hasToken && localUser) {
        // 验证token有效性并获取最新用户信息
        try {
          const currentUser = await authService.getCurrentUser();
          setUser(currentUser);
          setIsAuthenticated(true);
        } catch (error) {
          // token无效，清除本地存储
          authService.clearLocalStorage();
          setUser(null);
          setIsAuthenticated(false);
        }
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('Initialize auth error:', error);
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 登录
  const login = useCallback(async (credentials: LoginRequest) => {
    try {
      setIsLoading(true);
      const response = await authService.login(credentials);
      setUser(response.user);
      setIsAuthenticated(true);
      authStateManager.notifyStateChange();
    } catch (error) {
      setUser(null);
      setIsAuthenticated(false);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 注册
  const register = useCallback(async (userData: RegisterRequest) => {
    try {
      setIsLoading(true);
      await authService.register(userData);
      // 注册成功后不自动登录，需要用户手动登录
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 登出
  const logout = useCallback(async () => {
    try {
      setIsLoading(true);
      await authService.logout();
      setUser(null);
      setIsAuthenticated(false);
      authStateManager.notifyStateChange();
    } catch (error) {
      console.error('Logout error:', error);
      // 即使登出失败也要清除本地状态
      authService.clearLocalStorage();
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 刷新用户信息
  const refreshUser = useCallback(async () => {
    if (!isAuthenticated) return;

    try {
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      console.error('Refresh user error:', error);
      // 如果刷新失败，可能是token过期
      await logout();
    }
  }, [isAuthenticated, logout]);

  // 更新用户资料
  const updateProfile = useCallback(
    async (data: Partial<User>) => {
      if (!isAuthenticated) {
        throw new Error('User not authenticated');
      }

      try {
        const updatedUser = await authService.updateProfile(data);
        setUser(updatedUser);
        return updatedUser;
      } catch (error) {
        throw error;
      }
    },
    [isAuthenticated],
  );

  // 监听认证状态变化
  useEffect(() => {
    const handleAuthStateChange = (
      authenticated: boolean,
      userData: User | null,
    ) => {
      setIsAuthenticated(authenticated);
      setUser(userData);
    };

    authStateManager.addListener(handleAuthStateChange);

    return () => {
      authStateManager.removeListener(handleAuthStateChange);
    };
  }, []);

  // 初始化
  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  // 自动刷新token
  useEffect(() => {
    if (!isAuthenticated) return;

    const interval = setInterval(() => {
      authService.autoRefreshToken();
    }, 60000); // 每分钟检查一次

    return () => clearInterval(interval);
  }, [isAuthenticated]);

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
    updateProfile,
  };
};

export default useAuth;