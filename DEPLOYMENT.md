# 部署指南

## 生产环境部署

### 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM
- 20GB+ 磁盘空间

### 环境配置

1. 复制生产环境配置文件
```bash
cp .env.prod .env
```

2. 修改必要的环境变量
```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@db:5432/kb_prod

# Redis配置
REDIS_URL=redis://redis:6379/0

# 密钥配置
SECRET_KEY=your-secret-key-here
DJANGO_SECRET_KEY=your-django-secret-key-here

# 域名配置
ALLOWED_HOSTS=your-domain.com
NEXT_PUBLIC_API_URL=https://your-domain.com/api
```

### 部署步骤

1. 构建镜像
```bash
docker-compose -f docker-compose.yml build
```

2. 启动服务
```bash
docker-compose -f docker-compose.yml up -d
```

3. 数据库迁移
```bash
docker-compose -f docker-compose.yml exec backend python manage.py migrate
```

4. 收集静态文件
```bash
docker-compose -f docker-compose.yml exec backend python manage.py collectstatic --noinput
```

5. 创建超级用户
```bash
docker-compose -f docker-compose.yml exec backend python manage.py createsuperuser
```

### SSL证书配置

使用 Let's Encrypt 获取 SSL 证书：

```bash
# 安装 Certbot
docker run -it --rm --name certbot \
  -v "/etc/letsencrypt:/etc/letsencrypt" \
  -v "/var/lib/letsencrypt:/var/lib/letsencrypt" \
  certbot/certbot certonly --webroot \
  --webroot-path=/var/www/html \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email \
  -d your-domain.com
```

### 备份策略

1. 数据库备份
```bash
# 创建备份
docker-compose -f docker-compose.yml exec db pg_dump -U postgres kb_prod > backup.sql

# 恢复备份
docker-compose -f docker-compose.yml exec -T db psql -U postgres kb_prod < backup.sql
```

2. 文件备份
```bash
# 备份上传文件
tar -czf media_backup.tar.gz media/
```

### 监控和日志

查看服务状态：
```bash
docker-compose -f docker-compose.yml ps
```

查看日志：
```bash
# 查看所有服务日志
docker-compose -f docker-compose.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.yml logs -f backend
```

### 性能优化

1. 启用 Gunicorn 多进程
```bash
# 在 docker-compose.yml 中设置
environment:
  - GUNICORN_WORKERS=4
```

2. 配置 CDN
```bash
# 在 settings.py 中配置
STATIC_URL = 'https://cdn.your-domain.com/static/'
MEDIA_URL = 'https://cdn.your-domain.com/media/'
```

3. 数据库优化
```bash
# 定期执行 VACUUM
docker-compose -f docker-compose.yml exec db psql -U postgres -d kb_prod -c "VACUUM ANALYZE;"
```

## 故障排除

### 常见问题

1. **容器无法启动**
   - 检查端口冲突
   - 查看 Docker 日志
   - 确认环境变量配置正确

2. **数据库连接失败**
   - 检查数据库服务状态
   - 确认网络配置
   - 验证连接字符串

3. **静态文件加载失败**
   - 确认静态文件收集
   - 检查 Nginx 配置
   - 验证文件权限

### 获取帮助

- 查看日志文件
- 检查系统资源使用情况
- 联系技术支持团队