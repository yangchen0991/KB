import React, { useRef, useEffect } from 'react';

interface LiquidButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

const LiquidButton: React.FC<LiquidButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  disabled = false,
  className = '',
  type = 'button'
}) => {
  const buttonRef = useRef<HTMLButtonElement>(null);

  // 非牛顿流体按压反馈效果
  const handleMouseDown = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled) return;
    
    const button = buttonRef.current;
    if (!button) return;

    const rect = button.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // 创建涟漪效果
    const ripple = document.createElement('div');
    ripple.className = 'absolute rounded-full bg-white/30 pointer-events-none';
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    ripple.style.width = '0px';
    ripple.style.height = '0px';
    ripple.style.transform = 'translate(-50%, -50%)';
    ripple.style.transition = 'width 0.3s ease, height 0.3s ease, opacity 0.3s ease';

    button.appendChild(ripple);

    // 触发动画
    requestAnimationFrame(() => {
      ripple.style.width = '300px';
      ripple.style.height = '300px';
      ripple.style.opacity = '0';
    });

    // 清理
    setTimeout(() => {
      if (button.contains(ripple)) {
        button.removeChild(ripple);
      }
    }, 300);
  };

  // 陀螺仪微动态效果（模拟）
  useEffect(() => {
    const button = buttonRef.current;
    if (!button || disabled) return;

    let animationId: number;
    let startTime = Date.now();

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const x = Math.sin(elapsed * 0.001) * 0.5;
      const y = Math.cos(elapsed * 0.0015) * 0.3;
      
      button.style.transform = `perspective(1000px) rotateX(${y}deg) rotateY(${x}deg)`;
      
      animationId = requestAnimationFrame(animate);
    };

    const handleMouseEnter = () => {
      animate();
    };

    const handleMouseLeave = () => {
      cancelAnimationFrame(animationId);
      button.style.transform = '';
    };

    button.addEventListener('mouseenter', handleMouseEnter);
    button.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      cancelAnimationFrame(animationId);
      button.removeEventListener('mouseenter', handleMouseEnter);
      button.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, [disabled]);

  const getVariantStyles = () => {
    const variants = {
      primary: 'bg-gradient-to-br from-blue-500/80 to-indigo-600/80 hover:from-blue-600/90 hover:to-indigo-700/90',
      secondary: 'bg-gradient-to-br from-gray-500/80 to-gray-600/80 hover:from-gray-600/90 hover:to-gray-700/90',
      success: 'bg-gradient-to-br from-green-500/80 to-emerald-600/80 hover:from-green-600/90 hover:to-emerald-700/90',
      warning: 'bg-gradient-to-br from-yellow-500/80 to-orange-600/80 hover:from-yellow-600/90 hover:to-orange-700/90',
      danger: 'bg-gradient-to-br from-red-500/80 to-rose-600/80 hover:from-red-600/90 hover:to-rose-700/90'
    };
    return variants[variant];
  };

  const getSizeStyles = () => {
    const sizes = {
      sm: 'px-4 py-2 text-sm min-h-[36px] rounded-xl',
      md: 'px-6 py-3 text-base min-h-[44px] rounded-2xl',
      lg: 'px-8 py-4 text-lg min-h-[52px] rounded-3xl'
    };
    return sizes[size];
  };

  return (
    <button
      ref={buttonRef}
      type={type}
      onClick={onClick}
      onMouseDown={handleMouseDown}
      disabled={disabled}
      className={`
        relative overflow-hidden
        backdrop-blur-xl
        border-0
        text-white font-semibold
        cursor-pointer
        transition-all duration-300 ease-out
        transform-gpu
        hover:scale-105 hover:-translate-y-1
        active:scale-95 active:translate-y-0
        disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none
        shadow-lg hover:shadow-2xl
        ${getVariantStyles()}
        ${getSizeStyles()}
        ${className}
      `}
      style={{
        boxShadow: disabled ? 'none' : `
          0 8px 32px rgba(0, 0, 0, 0.12),
          inset 0 1px 0 rgba(255, 255, 255, 0.2),
          inset 0 -1px 0 rgba(0, 0, 0, 0.1)
        `
      }}
    >
      {/* 动态光泽层 */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
      
      {/* 内容 */}
      <span className="relative z-10 flex items-center justify-center gap-2">
        {children}
      </span>
    </button>
  );
};

export default LiquidButton;