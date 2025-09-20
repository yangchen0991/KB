import React, { useState, useRef, useEffect } from 'react';

interface LiquidInputProps {
  type?: 'text' | 'email' | 'password' | 'search' | 'tel' | 'url';
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  onFocus?: () => void;
  onBlur?: () => void;
  disabled?: boolean;
  error?: string;
  label?: string;
  icon?: React.ReactNode;
  className?: string;
  required?: boolean;
}

const LiquidInput: React.FC<LiquidInputProps> = ({
  type = 'text',
  placeholder,
  value,
  onChange,
  onFocus,
  onBlur,
  disabled = false,
  error,
  label,
  icon,
  className = '',
  required = false
}) => {
  const [focused, setFocused] = useState(false);
  const [hasValue, setHasValue] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setHasValue(!!value);
  }, [value]);

  const handleFocus = () => {
    setFocused(true);
    onFocus?.();
  };

  const handleBlur = () => {
    setFocused(false);
    onBlur?.();
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setHasValue(!!newValue);
    onChange?.(newValue);
  };

  return (
    <div className={`relative ${className}`}>
      {/* 标签 */}
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      {/* 输入框容器 */}
      <div className="relative">
        {/* 背景层 */}
        <div 
          className={`
            absolute inset-0 rounded-2xl transition-all duration-300 ease-out
            ${focused 
              ? 'bg-white/70 backdrop-blur-xl border-2 border-blue-500/50 shadow-lg shadow-blue-500/20' 
              : error
                ? 'bg-white/50 backdrop-blur-lg border-2 border-red-500/50'
                : 'bg-white/50 backdrop-blur-lg border border-white/30'
            }
          `}
          style={{
            backdropFilter: 'blur(12px) saturate(150%)',
            WebkitBackdropFilter: 'blur(12px) saturate(150%)'
          }}
        />

        {/* 聚焦时的光晕效果 */}
        {focused && (
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 blur-sm" />
        )}

        {/* 输入框 */}
        <div className="relative flex items-center">
          {/* 图标 */}
          {icon && (
            <div className={`absolute left-4 z-10 transition-colors duration-300 ${
              focused ? 'text-blue-600' : 'text-gray-400'
            }`}>
              {icon}
            </div>
          )}

          {/* 输入元素 */}
          <input
            ref={inputRef}
            type={type}
            value={value}
            onChange={handleChange}
            onFocus={handleFocus}
            onBlur={handleBlur}
            disabled={disabled}
            placeholder={placeholder}
            required={required}
            className={`
              w-full h-12 px-4 bg-transparent border-0 outline-none
              text-gray-900 placeholder-gray-400
              transition-all duration-300 ease-out
              rounded-2xl relative z-10
              ${icon ? 'pl-12' : 'pl-4'}
              ${disabled ? 'cursor-not-allowed opacity-50' : ''}
            `}
          />

          {/* 浮动标签效果 */}
          {placeholder && !hasValue && !focused && (
            <div className={`
              absolute left-4 pointer-events-none
              text-gray-400 transition-all duration-300 ease-out
              ${icon ? 'left-12' : 'left-4'}
            `}>
              {placeholder}
            </div>
          )}
        </div>

        {/* 底部装饰线 */}
        <div className={`
          absolute bottom-0 left-1/2 transform -translate-x-1/2
          h-0.5 bg-gradient-to-r from-blue-500 to-purple-500
          transition-all duration-300 ease-out
          ${focused ? 'w-full opacity-100' : 'w-0 opacity-0'}
        `} />
      </div>

      {/* 错误信息 */}
      {error && (
        <div className="mt-2 flex items-center space-x-2">
          <div className="w-1 h-1 bg-red-500 rounded-full" />
          <span className="text-sm text-red-600 font-medium">{error}</span>
        </div>
      )}

      {/* 聚焦时的微光效果 */}
      {focused && (
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-blue-500/50 to-transparent" />
      )}
    </div>
  );
};

export default LiquidInput;