# Knowledge Base System

一个现代化的知识库管理系统，基于 Django + Next.js 构建。

## 功能特性

- 📚 知识库管理
- 🔍 全文搜索
- 🏷️ 标签分类
- 👥 用户权限管理
- 📊 统计分析
- 🌐 多语言支持

## 技术栈

### 后端
- Django 4.2
- Django REST Framework
- PostgreSQL
- Redis
- Celery

### 前端
- Next.js 14
- TypeScript
- Tailwind CSS
- React Query

## 快速开始

1. 克隆项目
```bash
git clone https://github.com/yangchen0991/KB.git
cd KB
```

2. 环境配置
```bash
cp .env.dev .env
```

3. 启动服务
```bash
docker-compose up -d
```

4. 访问应用
- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- 管理后台: http://localhost:8000/admin

## 文档

- [部署指南](DEPLOYMENT.md)
- [设置指南](SETUP.md)

## 许可证

MIT License