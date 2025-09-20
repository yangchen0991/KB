import React, { useState } from 'react';
import { Layout, Menu, Avatar, Dropdown, Space, Typography, Button } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DashboardOutlined,
  FileTextOutlined,
  SearchOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  BellOutlined,
} from '@ant-design/icons';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '@/hooks/useAuth';
import { routes } from '@/config';

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout } = useAuth();
  const router = useRouter();

  // 菜单项配置
  const menuItems = [
    {
      key: routes.dashboard,
      icon: <DashboardOutlined />,
      label: <Link href={routes.dashboard}>仪表板</Link>,
    },
    {
      key: routes.documents,
      icon: <FileTextOutlined />,
      label: <Link href={routes.documents}>文档管理</Link>,
    },
    {
      key: routes.search,
      icon: <SearchOutlined />,
      label: <Link href={routes.search}>搜索</Link>,
    },
    {
      key: '/categories',
      icon: <SettingOutlined />,
      label: '分类管理',
      children: [
        {
          key: routes.categories,
          label: <Link href={routes.categories}>分类列表</Link>,
        },
        {
          key: routes.tags,
          label: <Link href={routes.tags}>标签管理</Link>,
        },
      ],
    },
  ];

  // 用户下拉菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: <Link href={routes.profile}>个人资料</Link>,
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: <Link href={routes.settings}>设置</Link>,
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: () => handleLogout(),
    },
  ];

  const handleLogout = async () => {
    try {
      await logout();
      router.push(routes.login);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 侧边栏 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={240}
        style={{
          background: '#fff',
          boxShadow: '2px 0 8px 0 rgba(29,35,41,.05)',
        }}
      >
        {/* Logo */}
        <div className="flex items-center justify-center h-16 border-b border-gray-200">
          {collapsed ? (
            <div className="text-2xl font-bold text-blue-600">KB</div>
          ) : (
            <Title level={4} className="!mb-0 text-blue-600">
              知识库系统
            </Title>
          )}
        </div>

        {/* 菜单 */}
        <Menu
          mode="inline"
          selectedKeys={[router.pathname]}
          items={menuItems}
          style={{ border: 'none', marginTop: 16 }}
        />
      </Sider>

      {/* 主要内容区域 */}
      <Layout>
        {/* 顶部导航 */}
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div className="flex items-center">
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              style={{ fontSize: '16px', width: 64, height: 64 }}
            />
          </div>

          <div className="flex items-center space-x-4">
            {/* 通知 */}
            <Button
              type="text"
              icon={<BellOutlined />}
              style={{ fontSize: '16px' }}
            />

            {/* 用户信息 */}
            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
              arrow
            >
              <Space className="cursor-pointer hover:bg-gray-50 px-3 py-2 rounded">
                <Avatar
                  size="small"
                  icon={<UserOutlined />}
                  src={user?.avatar}
                />
                <span className="text-gray-700">
                  {user?.first_name || user?.username || '用户'}
                </span>
              </Space>
            </Dropdown>
          </div>
        </Header>

        {/* 内容区域 */}
        <Content
          style={{
            margin: '24px',
            padding: '24px',
            background: '#fff',
            borderRadius: '8px',
            minHeight: 'calc(100vh - 112px)',
          }}
        >
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;