# 设置指南

## 开发环境设置

### 前置要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Git

### 后端设置

1. 创建虚拟环境
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

2. 安装依赖
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. 数据库设置
```bash
# 创建数据库
createdb kb_dev

# 运行迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser
```

4. 环境变量配置
```bash
cp .env.example .env
```

编辑 `.env` 文件：
```bash
DEBUG=True
DATABASE_URL=postgresql://localhost/kb_dev
SECRET_KEY=your-secret-key-here
REDIS_URL=redis://localhost:6379/0
```

5. 启动开发服务器
```bash
python manage.py runserver
```

### 前端设置

1. 安装依赖
```bash
cd frontend
npm install
```

2. 环境变量配置
```bash
cp .env.example .env.local
```

编辑 `.env.local` 文件：
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

3. 启动开发服务器
```bash
npm run dev
```

### Docker 开发环境

1. 启动所有服务
```bash
docker-compose -f docker-compose.dev.yml up -d
```

2. 查看服务状态
```bash
docker-compose -f docker-compose.dev.yml ps
```

3. 查看日志
```bash
docker-compose -f docker-compose.dev.yml logs -f
```

4. 停止服务
```bash
docker-compose -f docker-compose.dev.yml down
```

### 代码质量工具

1. 代码格式化
```bash
# 后端
black .
isort .

# 前端
npm run format
```

2. 代码检查
```bash
# 后端
flake8 .
mypy .

# 前端
npm run lint
```

3. 测试
```bash
# 后端
python manage.py test

# 前端
npm test
```

### Git 工作流

1. 创建功能分支
```bash
git checkout -b feature/your-feature-name
```

2. 提交更改
```bash
git add .
git commit -m "feat: add your feature description"
```

3. 推送到远程
```bash
git push origin feature/your-feature-name
```

4. 创建 Pull Request

### 预提交钩子

安装预提交钩子：
```bash
pre-commit install
```

手动运行预提交检查：
```bash
pre-commit run --all-files
```

### 环境变量参考

#### 后端环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| DEBUG | 调试模式 | False |
| SECRET_KEY | Django 密钥 | 必填 |
| DATABASE_URL | 数据库连接 | 必填 |
| REDIS_URL | Redis 连接 | 必填 |
| ALLOWED_HOSTS | 允许的主机 | * |
| CORS_ALLOWED_ORIGINS | CORS 源 | 空 |

#### 前端环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| NEXT_PUBLIC_API_URL | API 地址 | 必填 |
| NEXT_PUBLIC_SITE_URL | 站点地址 | http://localhost:3000 |

### 常见问题

1. **端口冲突**
   - 后端默认端口：8000
   - 前端默认端口：3000
   - 数据库默认端口：5432
   - Redis 默认端口：6379

2. **依赖安装失败**
   - 检查 Python/Node.js 版本
   - 清理缓存重新安装
   - 使用代理镜像源

3. **数据库连接失败**
   - 确认数据库服务运行
   - 检查连接字符串
   - 验证用户权限

### 获取帮助

- 查看文档
- 检查日志文件
- 在 GitHub 上创建 Issue