# 书签云同步服务

为智能书签助手 Chrome 扩展提供云端同步功能。

## 功能

- 用户注册/登录（邮箱+密码）
- 书签云端存储
- 每天自动同步
- 智能合并（无数据丢失）
- 管理后台（Arco Design Pro）

## 项目结构

```
bookmark-sync/
├── server/          # FastAPI 后端
├── admin/           # Vue 管理后台
├── k8s/             # K8s 部署配置
└── docker-compose.yml
```

## 本地开发

### 1. 启动服务

```bash
docker-compose up -d
```

### 2. 访问

- API: http://localhost:8000
- 管理后台: http://localhost:5173
- API 文档: http://localhost:8000/docs

### 3. 默认管理员

- 邮箱: admin@example.com
- 密码: admin123

## 部署到 K8s

### 1. 创建数据库

```sql
CREATE DATABASE bookmark_sync;
CREATE USER 'bookmark_sync'@'%' IDENTIFIED BY 'bookmark_sync_pass';
GRANT ALL PRIVILEGES ON bookmark_sync.* TO 'bookmark_sync'@'%';
FLUSH PRIVILEGES;
```

### 2. 构建镜像

```bash
# 服务端
cd server
docker build -t bookmark-sync-server:latest .

# 管理后台
cd ../admin
npm install
npm run build
docker build -t bookmark-sync-admin:latest .
```

### 3. 部署

```bash
kubectl apply -f k8s/deployment.yaml
```

### 4. 访问

- 管理后台: http://<node-ip>:30400

## 扩展配置

在 Chrome 扩展设置中配置同步服务器地址：

```
https://your-domain.com
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| POST /api/register | 注册 |
| POST /api/login | 登录 |
| POST /api/sync | 同步书签 |
| GET /api/bookmarks | 获取书签 |
| GET /api/status | 同步状态 |
| POST /admin/login | 管理员登录 |
| GET /admin/stats | 统计数据 |
| GET /admin/users | 用户列表 |
