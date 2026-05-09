#!/bin/bash

# 上传脚本
# 使用方法：./deploy/upload.sh

SERVER="152.136.116.187"
USER="root"  # 或者你的用户名
REMOTE_DIR="/opt/msi-hbp"

echo "=========================================="
echo "上传项目到服务器"
echo "=========================================="

# 排除不需要上传的文件
rsync -avz --progress \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'venv' \
    --exclude 'neo4j_data' \
    --exclude 'data/processed' \
    --exclude 'data/external' \
    --exclude '.env' \
    ./ ${USER}@${SERVER}:${REMOTE_DIR}/

echo ""
echo "上传完成！"
echo ""
echo "下一步："
echo "  ssh ${USER}@${SERVER}"
echo "  cd ${REMOTE_DIR}"
echo "  chmod +x deploy/deploy.sh"
echo "  ./deploy/deploy.sh"
