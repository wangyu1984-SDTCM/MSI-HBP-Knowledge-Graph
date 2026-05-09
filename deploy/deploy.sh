#!/bin/bash

# MSI-HBP 知识图谱部署脚本
# 服务器：152.136.116.187
# 域名：https://tcmhyperanx-knowledgegraph.cn/

set -e

echo "=========================================="
echo "MSI-HBP 知识图谱部署脚本"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_DIR="/opt/msi-hbp"
PROJECT_NAME="msi-hbp"
DOMAIN="tcmhyperanx-knowledgegraph.cn"

# 步骤1：检查系统环境
echo -e "\n${YELLOW}[1/8] 检查系统环境...${NC}"
if [ ! -f /etc/os-release ]; then
    echo -e "${RED}错误：无法识别操作系统${NC}"
    exit 1
fi

source /etc/os-release
echo "操作系统：$NAME $VERSION"

# 步骤2：安装系统依赖
echo -e "\n${YELLOW}[2/8] 安装系统依赖...${NC}"
if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv nginx git curl
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    sudo yum install -y python3 python3-pip nginx git curl
else
    echo -e "${RED}错误：不支持的包管理器${NC}"
    exit 1
fi

# 步骤3：创建项目目录
echo -e "\n${YELLOW}[3/8] 创建项目目录...${NC}"
sudo mkdir -p $PROJECT_DIR
sudo chown -R $USER:$USER $PROJECT_DIR
cd $PROJECT_DIR

# 步骤4：安装Python依赖
echo -e "\n${YELLOW}[4/8] 安装Python依赖...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 步骤5：配置环境变量
echo -e "\n${YELLOW}[5/8] 配置环境变量...${NC}"
if [ ! -f .env ]; then
    echo -e "${RED}警告：.env文件不存在，请手动创建并配置${NC}"
    cat > .env << 'EOF'
# LLM配置
MODEL_BASE_URL=https://api.siliconflow.cn/v1
MODEL_API_KEY=your-api-key-here
MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
MODEL_TEMPERATURE=0.1

# Neo4j配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password-here

# 项目配置
PROJECT_NAME=MSI-HBP
EOF
    echo -e "${YELLOW}请编辑 $PROJECT_DIR/.env 文件，填入实际配置${NC}"
fi

# 步骤6：安装和配置Neo4j
echo -e "\n${YELLOW}[6/8] 安装Neo4j...${NC}"
if ! command -v docker &> /dev/null; then
    echo "安装Docker..."
    curl -fsSL https://get.docker.com | bash
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
fi

echo "启动Neo4j容器..."
docker stop neo4j-msi-hbp 2>/dev/null || true
docker rm neo4j-msi-hbp 2>/dev/null || true

docker run -d \
    --name neo4j-msi-hbp \
    --restart always \
    -p 7474:7474 -p 7687:7687 \
    -v $PROJECT_DIR/neo4j_data:/data \
    -e NEO4J_AUTH=neo4j/msi-hbp-2024 \
    neo4j:latest

echo -e "${GREEN}Neo4j已启动，访问：http://152.136.116.187:7474${NC}"

# 步骤7：配置Nginx
echo -e "\n${YELLOW}[7/8] 配置Nginx...${NC}"

# 复制Nginx配置
sudo cp deploy/nginx.conf /etc/nginx/sites-available/$PROJECT_NAME
sudo ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/

# 创建SSL证书目录
sudo mkdir -p /etc/nginx/ssl

echo -e "${YELLOW}请将SSL证书放到以下位置：${NC}"
echo "  证书：/etc/nginx/ssl/tcmhyperanx-knowledgegraph.cn.crt"
echo "  私钥：/etc/nginx/ssl/tcmhyperanx-knowledgegraph.cn.key"
echo ""
echo -e "${YELLOW}如果没有SSL证书，可以使用Let's Encrypt免费申请：${NC}"
echo "  sudo apt-get install certbot python3-certbot-nginx"
echo "  sudo certbot --nginx -d $DOMAIN"

# 测试Nginx配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

# 步骤8：创建Systemd服务
echo -e "\n${YELLOW}[8/8] 创建Systemd服务...${NC}"

sudo tee /etc/systemd/system/msi-hbp.service > /dev/null << EOF
[Unit]
Description=MSI-HBP Knowledge Graph Web Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/streamlit run app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 重载systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start msi-hbp
sudo systemctl enable msi-hbp

# 检查服务状态
sleep 3
sudo systemctl status msi-hbp --no-pager

echo ""
echo -e "${GREEN}=========================================="
echo "部署完成！"
echo "==========================================${NC}"
echo ""
echo "访问地址："
echo "  - HTTPS: https://$DOMAIN"
echo "  - HTTP:  http://152.136.116.187:8080 (测试)"
echo "  - Neo4j: http://152.136.116.187:7474"
echo ""
echo "服务管理命令："
echo "  启动：sudo systemctl start msi-hbp"
echo "  停止：sudo systemctl stop msi-hbp"
echo "  重启：sudo systemctl restart msi-hbp"
echo "  状态：sudo systemctl status msi-hbp"
echo "  日志：sudo journalctl -u msi-hbp -f"
echo ""
echo "下一步："
echo "  1. 配置 .env 文件（API密钥）"
echo "  2. 配置SSL证书"
echo "  3. 运行知识抽取：source venv/bin/activate && python run_extraction.py"
echo "  4. 构建图谱：python build_graph.py"
echo ""
