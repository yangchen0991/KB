import React from 'react';

interface StatusIndicatorProps {
  status: 'connected' | 'disconnected' | 'checking' | 'warning';
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  showPulse?: boolean;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  size = 'md',
  showPulse = true
}) => {
  const getStatusConfig = () => {
    const configs = {
      connected: {
        color: 'from-emerald-400 to-green-500',
        shadow: 'shadow-emerald-500/40',
        text: '已连接',
        bgColor: 'bg-emerald-50',
        textColor: 'text-emerald-700'
      },
      disconnected: {
        color: 'from-red-400 to-rose-500',
        shadow: 'shadow-red-500/40',
        text: '连接失败',
        bgColor: 'bg-red-50',
        textColor: 'text-red-700'
      },
      checking: {
        color: 'from-amber-400 to-orange-500',
        shadow: 'shadow-amber-500/40',
        text: '检测中...',
        bgColor: 'bg-amber-50',
        textColor: 'text-amber-700'
      },
      warning: {
        color: 'from-yellow-400 to-amber-500',
        shadow: 'shadow-yellow-500/40',
        text: '警告',
        bgColor: 'bg-yellow-50',
        textColor: 'text-yellow-700'
      }
    };
    return configs[status];
  };

  const getSizeConfig = () => {
    const sizes = {
      sm: {
        dot: 'w-2 h-2',
        container: 'gap-2 text-xs',
        pulse: 'w-4 h-4'
      },
      md: {
        dot: 'w-3 h-3',
        container: 'gap-2 text-sm',
        pulse: 'w-6 h-6'
      },
      lg: {
        dot: 'w-4 h-4',
        container: 'gap-3 text-base',
        pulse: 'w-8 h-8'
      }
    };
    return sizes[size];
  };

  const statusConfig = getStatusConfig();
  const sizeConfig = getSizeConfig();

  return (
    <div className={`flex items-center ${sizeConfig.container}`}>
      {/* 状态指示点 */}
      <div className="relative flex items-center justify-center">
        {/* 主指示点 */}
        <div 
          className={`
            ${sizeConfig.dot} rounded-full
            bg-gradient-to-br ${statusConfig.color}
            ${statusConfig.shadow} shadow-lg
            relative z-10
          `}
        />
        
        {/* 脉冲效果 */}
        {showPulse && (status === 'checking' || status === 'connected') && (
          <div 
            className={`
              absolute ${sizeConfig.pulse} rounded-full
              bg-gradient-to-br ${statusConfig.color}
              opacity-20 animate-ping
            `}
          />
        )}
        
        {/* 外圈光晕 */}
        <div 
          className={`
            absolute ${sizeConfig.pulse} rounded-full
            bg-gradient-to-br ${statusConfig.color}
            opacity-10 blur-sm
          `}
        />
      </div>

      {/* 状态文本 */}
      {label && (
        <span className={`font-medium ${statusConfig.textColor}`}>
          {label}
        </span>
      )}
      
      {!label && (
        <span className={`font-medium ${statusConfig.textColor}`}>
          {statusConfig.text}
        </span>
      )}
    </div>
  );
};

export default StatusIndicator;