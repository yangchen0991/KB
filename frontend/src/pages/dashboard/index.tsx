import React, { useEffect, useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useAuth } from '@/hooks/useAuth';
import { routes } from '@/config';
import LiquidNavbar from '@/components/LiquidGlass/LiquidNavbar';
import LiquidCard from '@/components/LiquidGlass/LiquidCard';
import LiquidButton from '@/components/LiquidGlass/LiquidButton';
import StatusIndicator from '@/components/LiquidGlass/StatusIndicator';

interface DashboardStats {
  total_documents: number;
  total_users: number;
  documents_today: number;
  active_users: number;
}

interface SystemHealth {
  timestamp: string;
  database: {
    status: string;
    tables: number;
  };
  server: {
    status: string;
    status_code: number;
  };
  resources: {
    cpu_percent: number;
    memory_percent: number;
    disk_percent: number;
  };
}

const DashboardPage: React.FC = () => {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 获取仪表板数据
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 并行获取统计数据和健康状态
      const [healthResponse, statsResponse] = await Promise.allSettled([
        fetch('http://127.0.0.1:8001/api/v1/monitoring/health/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('kb_access_token')}`,
          },
        }),
        fetch('http://127.0.0.1:8001/api/v1/documents/stats/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('kb_access_token')}`,
          },
        }),
      ]);

      // 处理健康状态
      if (healthResponse.status === 'fulfilled' && healthResponse.value.ok) {
        const healthData = await healthResponse.value.json();
        setHealth(healthData);
      }

      // 处理统计数据
      if (statsResponse.status === 'fulfilled' && statsResponse.value.ok) {
        const statsData = await statsResponse.value.json();
        setStats(statsData);
      } else if (statsResponse.status === 'fulfilled' && statsResponse.value.status === 404) {
        // 如果统计接口不存在，使用模拟数据
        setStats({
          total_documents: 0,
          total_users: 1,
          documents_today: 0,
          active_users: 1,
        });
      }
    } catch (err: any) {
      console.error('Failed to fetch dashboard data:', err);
      setError('获取仪表板数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理登出
  const handleLogout = async () => {
    try {
      await logout();
      router.push(routes.login);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  // 检查认证状态
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(routes.login);
      return;
    }

    if (isAuthenticated) {
      fetchDashboardData();
    }
  }, [isAuthenticated, isLoading, router]);

  const navItems = [
    { label: '仪表板', href: '/dashboard', icon: '📊' },
    { label: '文档管理', href: '/documents', icon: '📄' },
    { label: '搜索', href: '/search', icon: '🔍' },
    { label: 'Liquid Demo', href: '/liquid-demo', icon: '✨' }
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        {/* 动态渐变背景 */}
        <div className="fixed inset-0 bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-purple-500/5 to-pink-500/5 animate-pulse" />
        </div>
        
        <div className="relative z-10 text-center">
          <div className="liquid-spinner mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">加载中...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // 重定向中
  }

  return (
    <>
      <Head>
        <title>仪表板 - 智能知识库系统</title>
        <meta name="description" content="智能知识库系统仪表板" />
      </Head>

      <div className="min-h-screen relative overflow-hidden">
        {/* 动态渐变背景 */}
        <div className="fixed inset-0 bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-purple-500/5 to-pink-500/5 animate-pulse" />
        </div>

        {/* 浮动装饰元素 */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-gradient-to-br from-blue-400/10 to-purple-400/10 rounded-full blur-3xl animate-pulse" />
          <div className="absolute top-3/4 right-1/4 w-96 h-96 bg-gradient-to-br from-purple-400/10 to-pink-400/10 rounded-full blur-3xl animate-pulse delay-1000" />
        </div>

        {/* 导航栏 */}
        <LiquidNavbar
          title="智能知识库系统"
          navItems={navItems}
          user={user}
          onLogout={handleLogout}
          isAuthenticated={isAuthenticated}
        />

        {/* 主要内容 */}
        <main className="relative z-10 pt-24 pb-12 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            
            {/* 页面标题 */}
            <div className="mb-8">
              <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                仪表板
              </h2>
              <p className="mt-2 text-gray-600">
                欢迎回来，{user?.first_name || user?.username}！
              </p>
            </div>

            {/* 错误提示 */}
            {error && (
              <LiquidCard className="mb-6 bg-red-50/80 border-red-200/50">
                <div className="text-red-800 text-sm font-medium">{error}</div>
              </LiquidCard>
            )}

            {/* 统计卡片 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <LiquidCard className="text-center">
                <div className="text-3xl mb-3">📄</div>
                <h3 className="text-sm font-medium text-gray-500 mb-1">总文档数</h3>
                <p className="text-2xl font-bold text-gray-900">
                  {loading ? '...' : stats?.total_documents || 0}
                </p>
              </LiquidCard>

              <LiquidCard className="text-center">
                <div className="text-3xl mb-3">👥</div>
                <h3 className="text-sm font-medium text-gray-500 mb-1">总用户数</h3>
                <p className="text-2xl font-bold text-gray-900">
                  {loading ? '...' : stats?.total_users || 0}
                </p>
              </LiquidCard>

              <LiquidCard className="text-center">
                <div className="text-3xl mb-3">📈</div>
                <h3 className="text-sm font-medium text-gray-500 mb-1">今日上传</h3>
                <p className="text-2xl font-bold text-gray-900">
                  {loading ? '...' : stats?.documents_today || 0}
                </p>
              </LiquidCard>

              <LiquidCard className="text-center">
                <div className="text-3xl mb-3">🟢</div>
                <h3 className="text-sm font-medium text-gray-500 mb-1">活跃用户</h3>
                <p className="text-2xl font-bold text-gray-900">
                  {loading ? '...' : stats?.active_users || 0}
                </p>
              </LiquidCard>
            </div>

            {/* 系统状态和快速操作 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* 系统健康状态 */}
              <LiquidCard>
                <h3 className="text-xl font-bold text-gray-900 mb-6">系统状态</h3>
                {health ? (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">数据库状态</span>
                      <StatusIndicator 
                        status={health.database.status === 'ok' ? 'connected' : 'disconnected'}
                        label={health.database.status === 'ok' ? '正常' : '异常'}
                        size="sm"
                      />
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">数据表数量</span>
                      <span className="text-sm font-medium">{health.database.tables}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">CPU使用率</span>
                      <span className="text-sm font-medium">{health.resources.cpu_percent}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">内存使用率</span>
                      <span className="text-sm font-medium">{health.resources.memory_percent}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">磁盘使用率</span>
                      <span className="text-sm font-medium">{health.resources.disk_percent}%</span>
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-8">
                    {loading ? (
                      <div className="flex items-center justify-center">
                        <div className="liquid-spinner mr-3"></div>
                        <span>加载中...</span>
                      </div>
                    ) : (
                      '无法获取系统状态'
                    )}
                  </div>
                )}
              </LiquidCard>

              {/* 快速操作 */}
              <LiquidCard>
                <h3 className="text-xl font-bold text-gray-900 mb-6">快速操作</h3>
                <div className="space-y-4">
                  <LiquidCard className="cursor-pointer hover:scale-[1.02] transition-transform duration-200">
                    <div className="flex items-center">
                      <div className="text-2xl mr-4">📤</div>
                      <div>
                        <div className="font-semibold text-gray-900">上传文档</div>
                        <div className="text-sm text-gray-600">添加新的文档到知识库</div>
                      </div>
                    </div>
                  </LiquidCard>
                  
                  <LiquidCard className="cursor-pointer hover:scale-[1.02] transition-transform duration-200">
                    <div className="flex items-center">
                      <div className="text-2xl mr-4">🔍</div>
                      <div>
                        <div className="font-semibold text-gray-900">搜索文档</div>
                        <div className="text-sm text-gray-600">在知识库中查找文档</div>
                      </div>
                    </div>
                  </LiquidCard>
                  
                  <LiquidCard className="cursor-pointer hover:scale-[1.02] transition-transform duration-200">
                    <div className="flex items-center">
                      <div className="text-2xl mr-4">⚙️</div>
                      <div>
                        <div className="font-semibold text-gray-900">系统设置</div>
                        <div className="text-sm text-gray-600">配置系统参数和权限</div>
                      </div>
                    </div>
                  </LiquidCard>
                </div>
              </LiquidCard>
            </div>

            {/* API连接测试 */}
            <LiquidCard>
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-gray-900">API连接测试</h3>
                <LiquidButton
                  variant="primary"
                  size="sm"
                  onClick={fetchDashboardData}
                  disabled={loading}
                >
                  {loading ? '🔄 测试中...' : '🔄 重新测试'}
                </LiquidButton>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 border border-white/30">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-gray-900">后端API</span>
                    <StatusIndicator 
                      status={health ? 'connected' : 'disconnected'}
                      size="sm"
                    />
                  </div>
                  <div className="text-sm text-gray-600">
                    http://127.0.0.1:8001
                  </div>
                </div>
                
                <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 border border-white/30">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-gray-900">用户认证</span>
                    <StatusIndicator 
                      status={isAuthenticated ? 'connected' : 'disconnected'}
                      size="sm"
                    />
                  </div>
                  <div className="text-sm text-gray-600">
                    JWT Token认证
                  </div>
                </div>
              </div>
            </LiquidCard>
          </div>
        </main>
      </div>
    </>
  );
};

export default DashboardPage;