/**
 * 格式化文件大小
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * 获取文件类型
 */
export const getFileType = (filename: string): string => {
  const extension = filename.split('.').pop()?.toLowerCase() || '';
  
  const typeMap: Record<string, string> = {
    pdf: 'pdf',
    doc: 'doc',
    docx: 'docx',
    txt: 'txt',
    jpg: 'jpg',
    jpeg: 'jpeg',
    png: 'png',
    tiff: 'tiff',
    bmp: 'bmp',
    gif: 'gif',
  };
  
  return typeMap[extension] || 'unknown';
};

/**
 * 格式化日期
 */
export const formatDate = (date: string | Date): string => {
  const d = new Date(date);
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * 截取文本
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

/**
 * 生成随机颜色
 */
export const generateRandomColor = (): string => {
  const colors = [
    '#1890ff', '#52c41a', '#fa8c16', '#722ed1',
    '#13c2c2', '#eb2f96', '#f5222d', '#faad14',
    '#2f54eb', '#a0d911', '#fa541c', '#9254de',
  ];
  
  return colors[Math.floor(Math.random() * colors.length)];
};

/**
 * 防抖函数
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

/**
 * 节流函数
 */
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};