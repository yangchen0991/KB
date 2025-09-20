import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import LiquidButton from './LiquidButton';

interface NavItem {
  label: string;
  href: string;
  icon?: string;
}

interface LiquidNavbarProps {
  title: string;
  navItems?: NavItem[];
  user?: {
    username?: string;
    first_name?: string;
    avatar?: string;
  } | null;
  onLogout?: () => void;
  isAuthenticated?: boolean;
}

const LiquidNavbar: React.FC<LiquidNavbarProps> = ({
  title,
  navItems = [],
  user,
  onLogout,
  isAuthenticated = false
}) => {
  const router = useRouter();
  const [scrolled, setScrolled] = useState(false);

  // 滚动效果
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav 
      className={`
        fixed top-0 left-0 right-0 z-50
        transition-all duration-500 ease-out
        ${scrolled 
          ? 'bg-white/80 backdrop-blur-2xl border-b border-black/5 shadow-lg' 
          : 'bg-white/60 backdrop-blur-xl border-b border-white/20'
        }
      `}
      style={{
        backdropFilter: 'blur(20px) saturate(180%)',
        WebkitBackdropFilter: 'blur(20px) saturate(180%)'
      }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo区域 */}
          <div className="flex items-center space-x-8">
            <Link href="/" className="flex items-center space-x-3 group">
              <div className="relative">
                {/* Logo图标 */}
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center transform group-hover:scale-110 transition-transform duration-300">
                  <span className="text-white font-bold text-sm">KB</span>
                </div>
                {/* 光晕效果 */}
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl blur-md opacity-0 group-hover:opacity-30 transition-opacity duration-300" />
              </div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                {title}
              </h1>
            </Link>

            {/* 导航菜单 */}
            {navItems.length > 0 && (
              <div className="hidden md:flex space-x-1">
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`
                      relative px-4 py-2 rounded-xl text-sm font-medium
                      transition-all duration-300 ease-out
                      hover:bg-white/40 hover:backdrop-blur-sm
                      ${router.pathname === item.href
                        ? 'text-blue-600 bg-blue-50/50'
                        : 'text-gray-700 hover:text-gray-900'
                      }
                    `}
                  >
                    {item.icon && <span className="mr-2">{item.icon}</span>}
                    {item.label}
                    
                    {/* 活跃状态指示器 */}
                    {router.pathname === item.href && (
                      <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-blue-600 rounded-full" />
                    )}
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* 用户区域 */}
          <div className="flex items-center space-x-4">
            {isAuthenticated && user ? (
              <>
                {/* 用户信息 */}
                <div className="hidden sm:flex items-center space-x-3">
                  {user.avatar ? (
                    <img
                      src={user.avatar}
                      alt="用户头像"
                      className="w-8 h-8 rounded-full border-2 border-white/50"
                    />
                  ) : (
                    <div className="w-8 h-8 bg-gradient-to-br from-gray-400 to-gray-600 rounded-full flex items-center justify-center">
                      <span className="text-white text-sm font-medium">
                        {(user.first_name || user.username || 'U').charAt(0).toUpperCase()}
                      </span>
                    </div>
                  )}
                  <span className="text-gray-700 font-medium">
                    欢迎, {user.first_name || user.username}
                  </span>
                </div>

                {/* 登出按钮 */}
                <LiquidButton
                  variant="secondary"
                  size="sm"
                  onClick={onLogout}
                  className="bg-gradient-to-r from-gray-500/80 to-gray-600/80"
                >
                  退出登录
                </LiquidButton>
              </>
            ) : (
              <LiquidButton
                variant="primary"
                size="sm"
                onClick={() => router.push('/auth/login')}
              >
                登录
              </LiquidButton>
            )}
          </div>
        </div>
      </div>

      {/* 底部光晕 */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-blue-500/20 to-transparent" />
    </nav>
  );
};

export default LiquidNavbar;