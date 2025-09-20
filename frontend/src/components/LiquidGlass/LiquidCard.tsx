import React, { useRef, useEffect, useState } from 'react';

interface LiquidCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
  gradient?: boolean;
}

const LiquidCard: React.FC<LiquidCardProps> = ({
  children,
  className = '',
  hover = true,
  onClick,
  gradient = false
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [mousePosition, setMousePosition] = useState({ x: 50, y: 50 });

  // 流体扩散动画
  useEffect(() => {
    const card = cardRef.current;
    if (!card || !hover) return;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = card.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      
      setMousePosition({ x, y });
      
      // 设置CSS自定义属性用于径向渐变
      card.style.setProperty('--mouse-x', `${x}%`);
      card.style.setProperty('--mouse-y', `${y}%`);
    };

    const handleMouseEnter = () => {
      card.classList.add('group');
    };

    const handleMouseLeave = () => {
      card.classList.remove('group');
      card.style.removeProperty('--mouse-x');
      card.style.removeProperty('--mouse-y');
    };

    card.addEventListener('mousemove', handleMouseMove);
    card.addEventListener('mouseenter', handleMouseEnter);
    card.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      card.removeEventListener('mousemove', handleMouseMove);
      card.removeEventListener('mouseenter', handleMouseEnter);
      card.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, [hover]);

  return (
    <div
      ref={cardRef}
      onClick={onClick}
      className={`
        relative overflow-hidden
        bg-white/60 backdrop-blur-xl
        border border-white/30
        rounded-3xl p-6
        transition-all duration-300 ease-out
        transform-gpu
        ${hover ? 'hover:scale-[1.02] hover:-translate-y-2 hover:shadow-2xl hover:border-blue-500/20' : ''}
        ${onClick ? 'cursor-pointer' : ''}
        ${gradient ? 'bg-gradient-to-br from-white/70 to-white/40' : ''}
        ${className}
      `}
      style={{
        boxShadow: `
          0 8px 32px rgba(0, 0, 0, 0.08),
          inset 0 1px 0 rgba(255, 255, 255, 0.4),
          inset 0 -1px 0 rgba(255, 255, 255, 0.1)
        `
      }}
    >
      {/* 流体扩散效果层 */}
      {hover && (
        <div 
          className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
          style={{
            background: `radial-gradient(
              circle 120px at var(--mouse-x, 50%) var(--mouse-y, 50%),
              rgba(59, 130, 246, 0.15) 0%,
              rgba(147, 51, 234, 0.1) 25%,
              transparent 50%
            )`
          }}
        />
      )}

      {/* 动态边框光晕 */}
      <div className="absolute inset-0 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
        <div className="absolute inset-0 rounded-3xl bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-pink-500/20 blur-sm" />
      </div>

      {/* 内容层 */}
      <div className="relative z-10">
        {children}
      </div>

      {/* 微光效果 */}
      <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-white/50 to-transparent" />
    </div>
  );
};

export default LiquidCard;