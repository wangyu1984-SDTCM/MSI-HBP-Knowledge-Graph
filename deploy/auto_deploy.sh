#!/bin/bash

# 自动化部署脚本
# 服务器：152.136.116.187
# 密码：Feng123456

set -e

SERVER="152.136.116.187"
PASSWORD="Feng123456"
USER="root"
REMOTE_DIR="/opt/msi-hbp"
DOMAIN="tcmhyperanx-knowledgegraph.cn"

echo "=========================================="
echo "MSI-HBP 自动化部署"
echo "=========================================="

# 安装sshpass（用于自动输入密码）
if ! command -v sshpass &> /dev/null; then
    echo "安装sshpass..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get install -y sshpass || sudo yum install -y sshpass
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install hudochenkov/sshpass/sshpass
    fi
fi

# 定义SSH命令
SSH_CMD="sshpass -p '$PASSWORD' ssh -o StrictHostKeyChecking=no $USER@$SERVER"
SCP_CMD="sshpass -p '$PASSWORD' scp -o StrictHostKeyChecking=no"

echo ""
echo "[1/6] 测试服务器连接..."
$SSH_CMD "echo '连接成功！'"

echo ""
echo "[2/6] 创建项目目录..."
$SSH_CMD "mkdir -p $REMOTE_DIR"

echo ""
echo "[3/6] 上传项目文件..."
sshpass -p "$PASSWORD" rsync -avz --progress \
    -e "ssh -o StrictHostKeyChecking=no" \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'venv' \
    --exclude 'neo4j_data' \
    --exclude 'data/processed/*' \
    --exclude 'data/external/*' \
    ./ ${USER}@${SERVER}:${REMOTE_DIR}/

echo ""
echo "[4/6] 安装系统依赖..."
$SSH_CMD << 'ENDSSH'
set -e

# 更新包管理器
apt-get update

# 安装基础依赖
apt-get install -y python3 python3-pip python3-venv nginx curl wget

# 安装Docker
if ! command -v docker &> /dev/null; then
    echo "安装Docker..."
    curl -fsSL https://get.docker.com | bash
    systemctl start docker
    systemctl enable docker
fi

echo "系统依赖安装完成！"
ENDSSH

echo ""
echo "[5/6] 配置和启动服务..."
$SSH_CMD << 'ENDSSH'
set -e
cd /opt/msi-hbp

# 创建Python虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install --upgrade pip
pip install -r requirements.txt

# 启动Neo4j
echo "启动Neo4j..."
docker stop neo4j-msi-hbp 2>/dev/null || true
docker rm neo4j-msi-hbp 2>/dev/null || true

docker run -d \
    --name neo4j-msi-hbp \
    --restart always \
    -p 7474:7474 -p 7687:7687 \
    -v /opt/msi-hbp/neo4j_data:/data \
    -e NEO4J_AUTH=neo4j/123456 \
    neo4j:latest

echo "等待Neo4j启动..."
sleep 10

# 配置Nginx
echo "配置Nginx..."
cp deploy/nginx.conf /etc/nginx/sites-available/msi-hbp
ln -sf /etc/nginx/sites-available/msi-hbp /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 创建临时自签名证书（如果没有SSL证书）
mkdir -p /etc/nginx/ssl
if [ ! -f /etc/nginx/ssl/tcmhyperanx-knowledgegraph.cn.crt ]; then
    echo "创建临时自签名证书..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/tcmhyperanx-knowledgegraph.cn.key \
        -out /etc/nginx/ssl/tcmhyperanx-knowledgegraph.cn.crt \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=MSI-HBP/CN=tcmhyperanx-knowledgegraph.cn"
fi

# 测试Nginx配置
nginx -t

# 重启Nginx
systemctl restart nginx
systemctl enable nginx

# 创建Systemd服务
cat > /etc/systemd/system/msi-hbp.service << 'EOF'
[Unit]
Description=MSI-HBP Knowledge Graph Web Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/msi-hbp
Environment="PATH=/opt/msi-hbp/venv/bin"
ExecStart=/opt/msi-hbp/venv/bin/streamlit run app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 重载systemd
systemctl daemon-reload

# 启动服务
systemctl start msi-hbp
systemctl enable msi-hbp

echo "服务配置完成！"
ENDSSH

echo ""
echo "[6/6] 配置防火墙..."
$SSH_CMD << 'ENDSSH'
# 配置防火墙
if command -v ufw &> /dev/null; then
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 7474/tcp
    ufw --force enable
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --permanent --add-port=7474/tcp
    firewall-cmd --reload
fi
ENDSSH

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  - HTTPS: https://tcmhyperanx-knowledgegraph.cn/"
echo "  - HTTP:  http://152.136.116.187/"
echo "  - Neo4j: http://152.136.116.187:7474"
echo ""
echo "Neo4j登录信息："
echo "  用户名: neo4j"
echo "  密码: 123456"
echo ""
echo "检查服务状态："
$SSH_CMD "systemctl status msi-hbp --no-pager"
echo ""
echo "查看日志："
echo "  ssh root@152.136.116.187"
echo "  journalctl -u msi-hbp -f"
echo ""
