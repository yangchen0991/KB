import React, { useState } from 'react';
import { Form, Input, Button, Checkbox, Alert, Divider } from 'antd';
import {
  UserOutlined,
  LockOutlined,
  EyeInvisibleOutlined,
  EyeTwoTone,
} from '@ant-design/icons';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '@/hooks/useAuth';
import { routes } from '@/config';
import { LoginRequest } from '@/types';

interface LoginFormProps {
  onSuccess?: () => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onSuccess }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (values: LoginRequest & { remember: boolean }) => {
    setLoading(true);
    setError(null);

    try {
      await login({
        email: values.email,
        password: values.password,
      });

      // 记住登录状态
      if (values.remember) {
        localStorage.setItem('remember_login', 'true');
      }

      // 登录成功后的处理
      if (onSuccess) {
        onSuccess();
      } else {
        const redirectTo =
          (router.query.redirect as string) || routes.dashboard;
        router.push(redirectTo);
      }
    } catch (err: any) {
      setError(err.message || '登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          登录到知识库系统
        </h1>
        <p className="text-gray-600">请输入您的账号信息</p>
      </div>

      {error && (
        <Alert
          message={error}
          type="error"
          showIcon
          closable
          className="mb-6"
          onClose={() => setError(null)}
        />
      )}

      <Form
        form={form}
        name="login"
        onFinish={handleSubmit}
        autoComplete="off"
        size="large"
        layout="vertical"
      >
        <Form.Item
          name="email"
          label="邮箱地址"
          rules={[
            { required: true, message: '请输入邮箱地址' },
            { type: 'email', message: '请输入有效的邮箱地址' },
          ]}
        >
          <Input
            prefix={<UserOutlined className="text-gray-400" />}
            placeholder="请输入邮箱地址"
            autoComplete="email"
          />
        </Form.Item>

        <Form.Item
          name="password"
          label="密码"
          rules={[
            { required: true, message: '请输入密码' },
            { min: 6, message: '密码至少6位字符' },
          ]}
        >
          <Input.Password
            prefix={<LockOutlined className="text-gray-400" />}
            placeholder="请输入密码"
            autoComplete="current-password"
            iconRender={(visible) =>
              visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />
            }
          />
        </Form.Item>

        <Form.Item>
          <div className="flex items-center justify-between">
            <Form.Item name="remember" valuePropName="checked" noStyle>
              <Checkbox>记住我</Checkbox>
            </Form.Item>
            <Link
              href="/auth/forgot-password"
              className="text-blue-600 hover:text-blue-500"
            >
              忘记密码？
            </Link>
          </div>
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            className="w-full h-12 text-base font-medium"
          >
            {loading ? '登录中...' : '登录'}
          </Button>
        </Form.Item>
      </Form>

      <Divider>或</Divider>

      <div className="text-center">
        <span className="text-gray-600">还没有账号？</span>
        <Link
          href={routes.register}
          className="ml-1 text-blue-600 hover:text-blue-500 font-medium"
        >
          立即注册
        </Link>
      </div>

      {/* 演示账号信息 */}
      <div className="mt-8 p-4 bg-blue-50 rounded-lg">
        <h3 className="text-sm font-medium text-blue-900 mb-2">演示账号</h3>
        <div className="text-xs text-blue-700 space-y-1">
          <div>邮箱: admin@example.com</div>
          <div>密码: admin123</div>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;
