#!/bin/bash

# 数据库备份脚本

set -e

# 配置
BACKUP_DIR="/app/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME=${DB_NAME:-knowledge_base}
DB_USER=${DB_USER:-postgres}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}

# 创建备份目录
mkdir -p $BACKUP_DIR

echo "🗄️  开始备份数据库..."

# 备份PostgreSQL数据库
PGPASSWORD=$DB_PASSWORD pg_dump \
    -h $DB_HOST \
    -p $DB_PORT \
    -U $DB_USER \
    -d $DB_NAME \
    --no-owner \
    --no-privileges \
    --clean \
    --if-exists \
    > $BACKUP_DIR/db_backup_$DATE.sql

# 压缩备份文件
gzip $BACKUP_DIR/db_backup_$DATE.sql

echo "✅ 数据库备份完成: $BACKUP_DIR/db_backup_$DATE.sql.gz"

# 备份媒体文件
if [ -d "/app/media" ]; then
    echo "📁 备份媒体文件..."
    tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz -C /app media/
    echo "✅ 媒体文件备份完成: $BACKUP_DIR/media_backup_$DATE.tar.gz"
fi

# 清理旧备份（保留7天）
echo "🧹 清理旧备份文件..."
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "✅ 备份任务完成！"