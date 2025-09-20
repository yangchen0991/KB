import React, { useEffect, useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import LiquidNavbar from '@/components/LiquidGlass/LiquidNavbar';
import LiquidCard from '@/components/LiquidGlass/LiquidCard';
import LiquidButton from '@/components/LiquidGlass/LiquidButton';
import StatusIndicator from '@/components/LiquidGlass/StatusIndicator';

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
  ports: {
    [key: string]: boolean;
  };
}

const HomePage: React.FC = () => {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');

  // 测试后端连接
  const testBackendConnection = async () => {
    try {
      setHealthLoading(true);
      setConnectionStatus('checking');
      
      const response = await fetch('http://127.0.0.1:8001/api/v1/monitoring/health/');
      
      if (response.ok) {
        const data = await response.json();
        setSystemHealth(data);
        setConnectionStatus('connected');
      } else {
        setConnectionStatus('disconnected');
      }
    } catch (error) {
      console.error('Backend connection test failed:', error);
      setConnectionStatus('disconnected');
    } finally {
      setHealthLoading(false);
    }
  };

  useEffect(() => {
    testBackendConnection();
    const interval = setInterval(testBackendConnection, 30000);
    return () => clearInterval(interval);
  }, []);

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

  return (
    <>
      <Head>
        <title>智能知识库系统</title>
        <meta name="description" content="企业级知识库管理系统" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
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
          <div className="absolute bottom-1/4 left-1/3 w-80 h-80 bg-gradient-to-br from-pink-400/10 to-orange-400/10 rounded-full blur-3xl animate-pulse delay-2000" />
        </div>

        {/* 导航栏 */}
        <LiquidNavbar
          title="智能知识库系统"
          navItems={navItems}
          user={user}
          onLogout={logout}
          isAuthenticated={isAuthenticated}
        />

        {/* 主要内容 */}
        <main className="relative z-10 pt-24 pb-12 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            
            {/* 欢迎区域 */}
            <div className="text-center mb-16">
              <h2 className="text-5xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent mb-6">
                欢迎使用智能知识库系统
              </h2>
              <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
                企业级文档管理、智能分类、全文搜索、工作流引擎
              </p>
              
              {!isAuthenticated && (
                <div className="flex flex-wrap justify-center gap-4">
                  <Link href="/auth/login">
                    <LiquidButton variant="primary" size="lg">
                      🚀 立即登录
                    </LiquidButton>
                  </Link>
                  <Link href="/auth/register">
                    <LiquidButton variant="secondary" size="lg">
                      📝 注册账号
                    </LiquidButton>
                  </Link>
                </div>
              )}

              {isAuthenticated && (
                <div className="flex justify-center">
                  <Link href="/dashboard">
                    <LiquidButton variant="primary" size="lg">
                      📊 进入系统
                    </LiquidButton>
                  </Link>
                </div>
              )}
            </div>

            {/* 系统状态 */}
            <LiquidCard className="mb-12" gradient>
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-bold text-gray-900">系统状态</h3>
                <LiquidButton
                  variant="primary"
                  size="sm"
                  onClick={testBackendConnection}
                  disabled={healthLoading}
                >
                  {healthLoading ? '🔄 检测中...' : '🔄 刷新状态'}
                </LiquidButton>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* 连接状态 */}
                <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 border border-white/30">
                  <h4 className="font-semibold text-gray-900 mb-4">后端连接</h4>
                  <div className="flex items-center justify-between">
                    <StatusIndicator 
                      status={connectionStatus} 
                      size="md"
                    />
                    <span className="text-sm text-gray-600">
                      http://127.0.0.1:8001
                    </span>
                  </div>
                </div>

                {/* 数据库状态 */}
                {systemHealth && (
                  <>
                    <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 border border-white/30">
                      <h4 className="font-semibold text-gray-900 mb-4">数据库</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>状态:</span>
                          <StatusIndicator 
                            status={systemHealth.database.status === 'ok' ? 'connected' : 'disconnected'}
                            label={systemHealth.database.status === 'ok' ? '正常' : '异常'}
                            size="sm"
                          />
                        </div>
                        <div className="flex justify-between">
                          <span>表数量:</span>
                          <span className="font-medium">{systemHealth.database.tables}</span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 border border-white/30">
                      <h4 className="font-semibold text-gray-900 mb-4">系统资源</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>CPU:</span>
                          <span className="font-medium">{systemHealth.resources.cpu_percent}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>内存:</span>
                          <span className="font-medium">{systemHealth.resources.memory_percent}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>磁盘:</span>
                          <span className="font-medium">{systemHealth.resources.disk_percent}%</span>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </LiquidCard>

            {/* 功能特性 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
              <LiquidCard className="text-center">
                <div className="text-4xl mb-4">📄</div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">文档管理</h3>
                <p className="text-gray-600 text-sm">支持多种文件格式上传、预览、下载和版本管理</p>
              </LiquidCard>

              <LiquidCard className="text-center">
                <div className="text-4xl mb-4">🔍</div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">智能搜索</h3>
                <p className="text-gray-600 text-sm">全文搜索、语义搜索、智能推荐和搜索分析</p>
              </LiquidCard>

              <LiquidCard className="text-center">
                <div className="text-4xl mb-4">🏷️</div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">智能分类</h3>
                <p className="text-gray-600 text-sm">AI自动分类、标签管理和分类规则配置</p>
              </LiquidCard>

              <LiquidCard className="text-center">
                <div className="text-4xl mb-4">⚡</div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">工作流引擎</h3>
                <p className="text-gray-600 text-sm">自定义工作流、审批流程和自动化处理</p>
              </LiquidCard>
            </div>

            {/* 演示账号信息 */}
            {!isAuthenticated && (
              <LiquidCard gradient>
                <h3 className="text-xl font-bold text-gray-900 mb-6">演示账号</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 border border-white/30">
                    <h4 className="font-semibold text-gray-800 mb-3">👑 管理员账号</h4>
                    <div className="space-y-2 text-sm">
                      <div><strong>邮箱:</strong> admin@example.com</div>
                      <div><strong>密码:</strong> admin123</div>
                    </div>
                  </div>
                  <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 border border-white/30">
                    <h4 className="font-semibold text-gray-800 mb-3">👤 普通用户</h4>
                    <div className="space-y-2 text-sm">
                      <div><strong>邮箱:</strong> user@example.com</div>
                      <div><strong>密码:</strong> user123</div>
                    </div>
                  </div>
                </div>
              </LiquidCard>
            )}
          </div>
        </main>

        {/* 页脚 */}
        <footer className="relative z-10 mt-12">
          <div className="bg-white/60 backdrop-blur-xl border-t border-white/30">
            <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
              <div className="text-center text-gray-600">
                <p>&copy; 2025 智能知识库系统. 版本 1.0.0</p>
                <p className="text-sm mt-2">基于 Liquid Glass 设计系统构建</p>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
};

export default HomePage;