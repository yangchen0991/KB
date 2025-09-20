import React, { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '@/hooks/useAuth';
import { routes } from '@/config';
import LiquidCard from '@/components/LiquidGlass/LiquidCard';
import LiquidButton from '@/components/LiquidGlass/LiquidButton';
import LiquidInput from '@/components/LiquidGlass/LiquidInput';
import StatusIndicator from '@/components/LiquidGlass/StatusIndicator';

const LoginPage: React.FC = () => {
  const router = useRouter();
  const { login, isLoading } = useAuth();
  
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [errors, setErrors] = useState<{[key: string]: string}>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // 清除对应字段的错误
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors: {[key: string]: string} = {};
    
    if (!formData.email) {
      newErrors.email = '请输入邮箱地址';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = '请输入有效的邮箱地址';
    }
    
    if (!formData.password) {
      newErrors.password = '请输入密码';
    } else if (formData.password.length < 6) {
      newErrors.password = '密码长度至少6位';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setIsSubmitting(true);
    
    try {
      await login({ email: formData.email, password: formData.password });
      router.push(routes.dashboard);
    } catch (error: any) {
      setErrors({ 
        general: error.message || '登录失败，请检查邮箱和密码' 
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const fillDemoAccount = (type: 'admin' | 'user') => {
    if (type === 'admin') {
      setFormData({
        email: 'admin@example.com',
        password: 'admin123'
      });
    } else {
      setFormData({
        email: 'user@example.com',
        password: 'user123'
      });
    }
    setErrors({});
  };

  return (
    <>
      <Head>
        <title>登录 - 智能知识库系统</title>
        <meta name="description" content="登录智能知识库系统" />
      </Head>

      <div className="min-h-screen relative overflow-hidden flex items-center justify-center">
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

        {/* 主要内容 */}
        <div className="relative z-10 w-full max-w-md px-6">
          
          {/* Logo区域 */}
          <div className="text-center mb-8">
            <Link href="/" className="inline-flex items-center space-x-3 group">
              <div className="relative">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center transform group-hover:scale-110 transition-transform duration-300">
                  <span className="text-white font-bold text-lg">KB</span>
                </div>
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl blur-md opacity-0 group-hover:opacity-30 transition-opacity duration-300" />
              </div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                智能知识库系统
              </h1>
            </Link>
          </div>

          {/* 登录表单 */}
          <LiquidCard gradient>
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">欢迎回来</h2>
              <p className="text-gray-600">请登录您的账户</p>
            </div>

            {/* 全局错误提示 */}
            {errors.general && (
              <div className="mb-6 bg-red-50/80 backdrop-blur-sm border border-red-200/50 rounded-2xl p-4">
                <div className="flex items-center">
                  <StatusIndicator status="disconnected" size="sm" />
                  <span className="ml-2 text-red-700 text-sm font-medium">{errors.general}</span>
                </div>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              <LiquidInput
                type="email"
                label="邮箱地址"
                placeholder="请输入邮箱"
                value={formData.email}
                onChange={(value) => handleInputChange('email', value)}
                error={errors.email}
                icon={<span>📧</span>}
                required
              />

              <LiquidInput
                type="password"
                label="密码"
                placeholder="请输入密码"
                value={formData.password}
                onChange={(value) => handleInputChange('password', value)}
                error={errors.password}
                icon={<span>🔒</span>}
                required
              />

              <LiquidButton
                type="submit"
                variant="primary"
                size="lg"
                disabled={isSubmitting || isLoading}
                className="w-full"
              >
                {isSubmitting || isLoading ? (
                  <div className="flex items-center justify-center">
                    <div className="liquid-spinner mr-2 w-5 h-5"></div>
                    登录中...
                  </div>
                ) : (
                  '🚀 登录'
                )}
              </LiquidButton>
            </form>

            {/* 演示账号 */}
            <div className="mt-8 pt-6 border-t border-white/30">
              <h3 className="text-sm font-semibold text-gray-700 mb-4 text-center">快速体验</h3>
              <div className="grid grid-cols-2 gap-3">
                <LiquidButton
                  variant="secondary"
                  size="sm"
                  onClick={() => fillDemoAccount('admin')}
                  className="text-xs"
                >
                  👑 管理员
                </LiquidButton>
                <LiquidButton
                  variant="secondary"
                  size="sm"
                  onClick={() => fillDemoAccount('user')}
                  className="text-xs"
                >
                  👤 普通用户
                </LiquidButton>
              </div>
            </div>

            {/* 注册链接 */}
            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                还没有账户？{' '}
                <Link 
                  href="/auth/register" 
                  className="font-medium text-blue-600 hover:text-blue-500 transition-colors"
                >
                  立即注册
                </Link>
              </p>
            </div>

            {/* 忘记密码 */}
            <div className="mt-4 text-center">
              <Link 
                href="/auth/forgot-password" 
                className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
              >
                忘记密码？
              </Link>
            </div>
          </LiquidCard>

          {/* 返回首页 */}
          <div className="mt-8 text-center">
            <Link 
              href="/" 
              className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 transition-colors"
            >
              <span className="mr-1">←</span>
              返回首页
            </Link>
          </div>
        </div>
      </div>
    </>
  );
};

export default LoginPage;