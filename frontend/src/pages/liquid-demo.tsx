import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useAuth } from '@/hooks/useAuth';
import LiquidNavbar from '@/components/LiquidGlass/LiquidNavbar';
import LiquidCard from '@/components/LiquidGlass/LiquidCard';
import LiquidButton from '@/components/LiquidGlass/LiquidButton';
import StatusIndicator from '@/components/LiquidGlass/StatusIndicator';
import LiquidInput from '@/components/LiquidGlass/LiquidInput';

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

const LiquidDemoPage: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const [searchValue, setSearchValue] = useState('');

  // 测试后端连接
  const testConnection = async () => {
    try {
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
      console.error('Connection test failed:', error);
      setConnectionStatus('disconnected');
    }
  };

  useEffect(() => {
    testConnection();
    const interval = setInterval(testConnection, 30000); // 每30秒检查一次
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { label: '仪表板', href: '/dashboard', icon: '📊' },
    { label: '文档管理', href: '/documents', icon: '📄' },
    { label: '搜索', href: '/search', icon: '🔍' },
    { label: 'Liquid Demo', href: '/liquid-demo', icon: '✨' }
  ];

  return (
    <>
      <Head>
        <title>Liquid Glass Design System - 智能知识库系统</title>
        <meta name="description" content="基于iOS 26 Liquid Glass设计理念的现代化UI界面" />
      </Head>

      {/* 动态渐变背景 */}
      <div className="min-h-screen relative overflow-hidden">
        {/* 背景层 */}
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
            
            {/* 标题区域 */}
            <div className="text-center mb-16">
              <h1 className="text-5xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent mb-6">
                Liquid Glass Design System
              </h1>
              <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
                基于苹果iOS 26最新设计理念"Liquid Glass"的现代化UI界面设计，
                实现液体玻璃效果、动态光泽、流体动画等核心特性
              </p>
              
              <div className="flex flex-wrap justify-center gap-4">
                <LiquidButton variant="primary" size="lg">
                  ✨ 体验Demo
                </LiquidButton>
                <LiquidButton variant="secondary" size="lg">
                  📖 查看文档
                </LiquidButton>
              </div>
            </div>

            {/* 系统状态卡片 */}
            <LiquidCard className="mb-12" gradient>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900">系统状态监控</h2>
                <LiquidButton variant="primary" size="sm" onClick={testConnection}>
                  🔄 刷新状态
                </LiquidButton>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* 连接状态 */}
                <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 border border-white/30">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-gray-800">后端连接</h3>
                    <StatusIndicator 
                      status={connectionStatus} 
                      size="md"
                    />
                  </div>
                  <p className="text-sm text-gray-600">
                    API服务器: http://127.0.0.1:8001
                  </p>
                </div>

                {/* 数据库状态 */}
                <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 border border-white/30">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-gray-800">数据库</h3>
                    <StatusIndicator 
                      status={systemHealth?.database.status === 'ok' ? 'connected' : 'disconnected'} 
                      size="md"
                    />
                  </div>
                  <p className="text-sm text-gray-600">
                    表数量: {systemHealth?.database.tables || 0}
                  </p>
                </div>

                {/* 系统资源 */}
                <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 border border-white/30">
                  <h3 className="font-semibold text-gray-800 mb-4">系统资源</h3>
                  {systemHealth ? (
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
                  ) : (
                    <p className="text-sm text-gray-500">加载中...</p>
                  )}
                </div>
              </div>
            </LiquidCard>

            {/* 组件展示区域 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
              
              {/* 按钮组件展示 */}
              <LiquidCard>
                <h3 className="text-xl font-bold text-gray-900 mb-6">流体按钮组件</h3>
                <div className="space-y-4">
                  <div className="flex flex-wrap gap-3">
                    <LiquidButton variant="primary" size="sm">Primary Small</LiquidButton>
                    <LiquidButton variant="secondary" size="sm">Secondary</LiquidButton>
                    <LiquidButton variant="success" size="sm">Success</LiquidButton>
                  </div>
                  <div className="flex flex-wrap gap-3">
                    <LiquidButton variant="warning" size="md">Warning Medium</LiquidButton>
                    <LiquidButton variant="danger" size="md">Danger</LiquidButton>
                  </div>
                  <div className="flex flex-wrap gap-3">
                    <LiquidButton variant="primary" size="lg">Large Button</LiquidButton>
                    <LiquidButton variant="primary" size="lg" disabled>Disabled</LiquidButton>
                  </div>
                </div>
              </LiquidCard>

              {/* 输入框组件展示 */}
              <LiquidCard>
                <h3 className="text-xl font-bold text-gray-900 mb-6">液体玻璃输入框</h3>
                <div className="space-y-4">
                  <LiquidInput
                    label="搜索文档"
                    placeholder="输入关键词搜索..."
                    value={searchValue}
                    onChange={setSearchValue}
                    icon={<span>🔍</span>}
                  />
                  <LiquidInput
                    type="email"
                    label="邮箱地址"
                    placeholder="请输入邮箱"
                    icon={<span>📧</span>}
                    required
                  />
                  <LiquidInput
                    type="password"
                    label="密码"
                    placeholder="请输入密码"
                    icon={<span>🔒</span>}
                  />
                  <LiquidInput
                    label="错误示例"
                    placeholder="这是一个错误示例"
                    error="请输入有效的内容"
                    icon={<span>⚠️</span>}
                  />
                </div>
              </LiquidCard>
            </div>

            {/* 特性展示 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
              <LiquidCard className="text-center">
                <div className="text-4xl mb-4">💧</div>
                <h3 className="font-bold text-gray-900 mb-2">液体玻璃效果</h3>
                <p className="text-sm text-gray-600">45-65%透明度范围的半透明材质，营造深度感</p>
              </LiquidCard>

              <LiquidCard className="text-center">
                <div className="text-4xl mb-4">✨</div>
                <h3 className="font-bold text-gray-900 mb-2">动态光泽</h3>
                <p className="text-sm text-gray-600">随交互产生0.5-1.5度的微动态变化效果</p>
              </LiquidCard>

              <LiquidCard className="text-center">
                <div className="text-4xl mb-4">🌊</div>
                <h3 className="font-bold text-gray-900 mb-2">流体动画</h3>
                <p className="text-sm text-gray-600">200-300ms的自然流畅过渡动画</p>
              </LiquidCard>

              <LiquidCard className="text-center">
                <div className="text-4xl mb-4">🎯</div>
                <h3 className="font-bold text-gray-900 mb-2">无障碍设计</h3>
                <p className="text-sm text-gray-600">符合WCAG 2.1 AA标准的无障碍体验</p>
              </LiquidCard>
            </div>

            {/* 技术规范 */}
            <LiquidCard>
              <h3 className="text-2xl font-bold text-gray-900 mb-6">技术实现规范</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <h4 className="font-semibold text-gray-800 mb-3">视觉设计规范</h4>
                  <ul className="space-y-2 text-sm text-gray-600">
                    <li>• 半透明材质：45-65%透明度范围</li>
                    <li>• 动态光泽：0.5-1.5度微动态变化</li>
                    <li>• 色彩系统：苹果标准色板+10%透明度</li>
                    <li>• 磨砂玻璃：backdrop-filter blur效果</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-800 mb-3">交互体验标准</h4>
                  <ul className="space-y-2 text-sm text-gray-600">
                    <li>• 触控热区：最小44x44pt</li>
                    <li>• 动画时长：200-300ms</li>
                    <li>• 按压形变：15%±3%幅度</li>
                    <li>• 流体反馈：非牛顿流体算法</li>
                  </ul>
                </div>
              </div>
            </LiquidCard>

          </div>
        </main>
      </div>

      {/* 引入液体玻璃样式 */}
      <style jsx global>{`
        @import url('/src/styles/liquid-glass.css');
      `}</style>
    </>
  );
};

export default LiquidDemoPage;