# MSI-HBP 部署指南

## 服务器信息
- **IP**: 152.136.116.187
- **域名**: https://tcmhyperanx-knowledgegraph.cn/
- **端口**: 8080 (内部), 443 (外部HTTPS)

## 快速部署

### 方式1：自动部署（推荐）

```bash
# 1. 上传项目到服务器
./deploy/upload.sh

# 2. SSH登录服务器
ssh root@152.136.116.187

# 3. 进入项目目录
cd /opt/msi-hbp

# 4. 运行部署脚本
chmod +x deploy/deploy.sh
./deploy/deploy.sh

# 5. 配置.env文件
nano .env
# 填入API密钥和Neo4j密码

# 6. 重启服务
sudo systemctl restart msi-hbp
```

### 方式2：手动部署

#### 1. 上传项目
```bash
# 在本地执行
scp -r ./ root@152.136.116.187:/opt/msi-hbp/
```

#### 2. 安装依赖
```bash
# SSH登录服务器
ssh root@152.136.116.187

# 安装系统依赖
apt-get update
apt-get install -y python3 python3-pip python3-venv nginx docker.io

# 创建虚拟环境
cd /opt/msi-hbp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. 启动Neo4j
```bash
docker run -d \
    --name neo4j-msi-hbp \
    --restart always \
    -p 7474:7474 -p 7687:7687 \
    -v /opt/msi-hbp/neo4j_data:/data \
    -e NEO4J_AUTH=neo4j/msi-hbp-2024 \
    neo4j:latest
```

#### 4. 配置Nginx
```bash
# 复制配置文件
cp deploy/nginx.conf /etc/nginx/sites-available/msi-hbp
ln -s /etc/nginx/sites-available/msi-hbp /etc/nginx/sites-enabled/

# 配置SSL证书（使用Let's Encrypt）
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d tcmhyperanx-knowledgegraph.cn

# 重启Nginx
nginx -t
systemctl restart nginx
```

#### 5. 创建系统服务
```bash
# 创建服务文件
cat > /etc/systemd/system/msi-hbp.service << 'EOF'
[Unit]
Description=MSI-HBP Knowledge Graph
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/msi-hbp
Environment="PATH=/opt/msi-hbp/venv/bin"
ExecStart=/opt/msi-hbp/venv/bin/streamlit run app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
systemctl daemon-reload
systemctl start msi-hbp
systemctl enable msi-hbp
```

#### 6. 配置环境变量
```bash
nano /opt/msi-hbp/.env
```

填入：
```env
MODEL_BASE_URL=https://api.siliconflow.cn/v1
MODEL_API_KEY=sk-your-key-here
MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
MODEL_TEMPERATURE=0.1

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=msi-hbp-2024

PROJECT_NAME=MSI-HBP
```

#### 7. 初始化数据
```bash
cd /opt/msi-hbp
source venv/bin/activate

# 运行知识抽取
python run_extraction.py

# 构建图谱
python build_graph.py
```

## SSL证书配置

### 使用Let's Encrypt（免费）
```bash
# 安装certbot
apt-get install -y certbot python3-certbot-nginx

# 申请证书
certbot --nginx -d tcmhyperanx-knowledgegraph.cn

# 自动续期
certbot renew --dry-run
```

### 使用自有证书
```bash
# 将证书放到指定位置
cp your.crt /etc/nginx/ssl/tcmhyperanx-knowledgegraph.cn.crt
cp your.key /etc/nginx/ssl/tcmhyperanx-knowledgegraph.cn.key

# 设置权限
chmod 600 /etc/nginx/ssl/tcmhyperanx-knowledgegraph.cn.key
```

## 服务管理

```bash
# 启动服务
systemctl start msi-hbp

# 停止服务
systemctl stop msi-hbp

# 重启服务
systemctl restart msi-hbp

# 查看状态
systemctl status msi-hbp

# 查看日志
journalctl -u msi-hbp -f

# 查看Nginx日志
tail -f /var/log/nginx/tcmhyperanx_access.log
tail -f /var/log/nginx/tcmhyperanx_error.log
```

## 防火墙配置

```bash
# Ubuntu/Debian (ufw)
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 7474/tcp  # Neo4j浏览器（可选）
ufw enable

# CentOS/RHEL (firewalld)
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --permanent --add-port=7474/tcp
firewall-cmd --reload
```

## 故障排查

### 1. 服务无法启动
```bash
# 查看详细日志
journalctl -u msi-hbp -n 50

# 检查端口占用
netstat -tlnp | grep 8080

# 手动启动测试
cd /opt/msi-hbp
source venv/bin/activate
streamlit run app.py
```

### 2. Nginx 502错误
```bash
# 检查Streamlit是否运行
systemctl status msi-hbp

# 检查端口
curl http://127.0.0.1:8080

# 查看Nginx错误日志
tail -f /var/log/nginx/tcmhyperanx_error.log
```

### 3. Neo4j连接失败
```bash
# 检查Neo4j容器
docker ps | grep neo4j

# 查看Neo4j日志
docker logs neo4j-msi-hbp

# 重启Neo4j
docker restart neo4j-msi-hbp
```

## 性能优化

### 1. Nginx缓存
已在配置中启用静态文件缓存

### 2. Streamlit优化
```bash
# 修改 .streamlit/config.toml
[server]
maxUploadSize = 200
enableCORS = false
enableXsrfProtection = true
```

### 3. Neo4j优化
```bash
# 增加内存配置
docker run -d \
    --name neo4j-msi-hbp \
    -e NEO4J_dbms_memory_heap_initial__size=512m \
    -e NEO4J_dbms_memory_heap_max__size=2G \
    ...
```

## 监控

### 系统监控
```bash
# 安装htop
apt-get install htop

# 查看资源使用
htop
```

### 日志监控
```bash
# 实时查看应用日志
journalctl -u msi-hbp -f

# 实时查看Nginx日志
tail -f /var/log/nginx/tcmhyperanx_access.log
```

## 备份

### 备份Neo4j数据
```bash
# 停止Neo4j
docker stop neo4j-msi-hbp

# 备份数据
tar -czf neo4j_backup_$(date +%Y%m%d).tar.gz /opt/msi-hbp/neo4j_data/

# 启动Neo4j
docker start neo4j-msi-hbp
```

### 备份项目文件
```bash
tar -czf msi-hbp_backup_$(date +%Y%m%d).tar.gz \
    --exclude='venv' \
    --exclude='neo4j_data' \
    /opt/msi-hbp/
```

## 更新部署

```bash
# 1. 备份当前版本
cd /opt/msi-hbp
tar -czf ../msi-hbp_backup_$(date +%Y%m%d).tar.gz .

# 2. 上传新版本
# 在本地执行
./deploy/upload.sh

# 3. 重启服务
ssh root@152.136.116.187
systemctl restart msi-hbp
```

## 访问地址

- **Web界面**: https://tcmhyperanx-knowledgegraph.cn/
- **Neo4j浏览器**: http://152.136.116.187:7474
- **服务器IP**: http://152.136.116.187:8080 (测试用)

## 联系方式

如有问题，请联系管理员。
