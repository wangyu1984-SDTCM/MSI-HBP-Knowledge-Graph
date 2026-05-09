# MSI-HBP 自动化部署脚本 (Windows PowerShell)
# 服务器：152.136.116.187

$SERVER = "152.136.116.187"
$PASSWORD = "Feng123456"
$USER = "root"
$REMOTE_DIR = "/opt/msi-hbp"

Write-Host "==========================================" -ForegroundColor Green
Write-Host "MSI-HBP 自动化部署" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# 检查是否安装了必要工具
Write-Host "[检查] 检查必要工具..." -ForegroundColor Yellow

# 检查SSH
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Write-Host "错误：未找到SSH命令，请安装OpenSSH客户端" -ForegroundColor Red
    Write-Host "安装方法：设置 -> 应用 -> 可选功能 -> 添加功能 -> OpenSSH客户端" -ForegroundColor Yellow
    exit 1
}

# 检查SCP
if (-not (Get-Command scp -ErrorAction SilentlyContinue)) {
    Write-Host "错误：未找到SCP命令" -ForegroundColor Red
    exit 1
}

Write-Host "✓ SSH和SCP已安装" -ForegroundColor Green
Write-Host ""

# 步骤1：测试连接
Write-Host "[1/6] 测试服务器连接..." -ForegroundColor Yellow
$env:SSHPASS = $PASSWORD
$testCmd = "echo '连接成功'"
$result = echo y | plink -ssh -pw $PASSWORD ${USER}@${SERVER} $testCmd 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 服务器连接成功" -ForegroundColor Green
} else {
    Write-Host "提示：首次连接需要接受服务器密钥" -ForegroundColor Yellow
}
Write-Host ""

# 步骤2：创建目录
Write-Host "[2/6] 创建项目目录..." -ForegroundColor Yellow
echo y | plink -ssh -pw $PASSWORD ${USER}@${SERVER} "mkdir -p $REMOTE_DIR"
Write-Host "✓ 目录创建完成" -ForegroundColor Green
Write-Host ""

# 步骤3：上传文件
Write-Host "[3/6] 上传项目文件..." -ForegroundColor Yellow
Write-Host "正在上传，请稍候..." -ForegroundColor Cyan

# 使用WinSCP或pscp上传
$excludes = @("__pycache__", "*.pyc", "venv", "neo4j_data", ".git")

# 创建临时批处理文件用于上传
$uploadScript = @"
@echo off
cd /d "%~dp0\.."
pscp -r -pw $PASSWORD -batch ^
    -x __pycache__ -x *.pyc -x venv -x neo4j_data -x .git ^
    * ${USER}@${SERVER}:${REMOTE_DIR}/
"@

$uploadScript | Out-File -FilePath "deploy\upload_temp.bat" -Encoding ASCII
& "deploy\upload_temp.bat"
Remove-Item "deploy\upload_temp.bat"

Write-Host "✓ 文件上传完成" -ForegroundColor Green
Write-Host ""

# 步骤4：安装依赖
Write-Host "[4/6] 安装系统依赖..." -ForegroundColor Yellow

$installScript = @'
set -e
export DEBIAN_FRONTEND=noninteractive

# 更新包管理器
apt-get update -qq

# 安装基础依赖
apt-get install -y -qq python3 python3-pip python3-venv nginx curl wget

# 安装Docker
if ! command -v docker &> /dev/null; then
    echo "安装Docker..."
    curl -fsSL https://get.docker.com | bash
    systemctl start docker
    systemctl enable docker
fi

echo "系统依赖安装完成！"
'@

echo y | plink -ssh -pw $PASSWORD ${USER}@${SERVER} $installScript

Write-Host "✓ 系统依赖安装完成" -ForegroundColor Green
Write-Host ""

# 步骤5：配置服务
Write-Host "[5/6] 配置和启动服务..." -ForegroundColor Yellow

$setupScript = @'
set -e
cd /opt/msi-hbp

# 创建Python虚拟环境
echo "创建Python虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
echo "安装Python依赖..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

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
sleep 15

# 配置Nginx
echo "配置Nginx..."
cp deploy/nginx.conf /etc/nginx/sites-available/msi-hbp
ln -sf /etc/nginx/sites-available/msi-hbp /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 创建SSL证书目录
mkdir -p /etc/nginx/ssl

# 创建临时自签名证书
if [ ! -f /etc/nginx/ssl/tcmhyperanx-knowledgegraph.cn.crt ]; then
    echo "创建临时SSL证书..."
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

echo "等待服务启动..."
sleep 5

echo "服务配置完成！"
'@

echo y | plink -ssh -pw $PASSWORD ${USER}@${SERVER} $setupScript

Write-Host "✓ 服务配置完成" -ForegroundColor Green
Write-Host ""

# 步骤6：配置防火墙
Write-Host "[6/6] 配置防火墙..." -ForegroundColor Yellow

$firewallScript = @'
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
echo "防火墙配置完成"
'@

echo y | plink -ssh -pw $PASSWORD ${USER}@${SERVER} $firewallScript

Write-Host "✓ 防火墙配置完成" -ForegroundColor Green
Write-Host ""

# 完成
Write-Host "==========================================" -ForegroundColor Green
Write-Host "部署完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "访问地址：" -ForegroundColor Cyan
Write-Host "  - HTTPS: https://tcmhyperanx-knowledgegraph.cn/" -ForegroundColor White
Write-Host "  - HTTP:  http://152.136.116.187/" -ForegroundColor White
Write-Host "  - Neo4j: http://152.136.116.187:7474" -ForegroundColor White
Write-Host ""
Write-Host "Neo4j登录信息：" -ForegroundColor Cyan
Write-Host "  用户名: neo4j" -ForegroundColor White
Write-Host "  密码: 123456" -ForegroundColor White
Write-Host ""
Write-Host "检查服务状态：" -ForegroundColor Cyan
echo y | plink -ssh -pw $PASSWORD ${USER}@${SERVER} "systemctl status msi-hbp --no-pager"
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "  1. 访问 https://tcmhyperanx-knowledgegraph.cn/ 测试" -ForegroundColor White
Write-Host "  2. 如需正式SSL证书，运行：" -ForegroundColor White
Write-Host "     ssh root@152.136.116.187" -ForegroundColor Gray
Write-Host "     apt-get install certbot python3-certbot-nginx" -ForegroundColor Gray
Write-Host "     certbot --nginx -d tcmhyperanx-knowledgegraph.cn" -ForegroundColor Gray
Write-Host ""
