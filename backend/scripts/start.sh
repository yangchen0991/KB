#!/bin/bash

# 知识库系统启动脚本

set -e

echo "🚀 启动知识库系统..."

# 检查环境变量
if [ -z "$DJANGO_SETTINGS_MODULE" ]; then
    export DJANGO_SETTINGS_MODULE="knowledge_base.settings"
fi

# 等待数据库就绪
echo "⏳ 等待数据库就绪..."
python manage.py wait_for_db

# 执行数据库迁移
echo "📊 执行数据库迁移..."
python manage.py migrate --noinput

# 收集静态文件
echo "📁 收集静态文件..."
python manage.py collectstatic --noinput

# 创建超级用户（如果不存在）
echo "👤 检查超级用户..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('创建超级用户: admin/admin123')
else:
    print('超级用户已存在')
"

# 启动Celery Worker（后台）
echo "🔄 启动Celery Worker..."
celery -A knowledge_base worker --loglevel=info --detach

# 启动Celery Beat（后台）
echo "⏰ 启动Celery Beat..."
celery -A knowledge_base beat --loglevel=info --detach

# 启动Django服务器
echo "🌐 启动Django服务器..."
if [ "$DEBUG" = "True" ]; then
    python manage.py runserver 0.0.0.0:8000
else
    gunicorn knowledge_base.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 4 \
        --worker-class gevent \
        --worker-connections 1000 \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --timeout 30 \
        --keep-alive 2 \
        --log-level info \
        --access-logfile - \
        --error-logfile -
fi