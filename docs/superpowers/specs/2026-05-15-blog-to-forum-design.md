# Blog → Forum 改造设计文档

> 2026-05-15 | 决策: 渐进改造（复用基础设施，重命名+扩展）

## 目标

将个人技术博客改造为无版块的扁平论坛系统。所有注册用户可发帖/回复/点赞。

## 核心决策汇总

| 维度 | 决策 |
|------|------|
| 论坛类型 | 无版块扁平论坛（简单发帖） |
| 发帖权限 | 所有注册用户 |
| 用户角色 | 用户 + 管理员 |
| 旧数据 | 保留用户账号，清空帖子/评论 |
| 首页布局 | 最新帖子优先 |
| 帖子管理 | 基础管理（无置顶/锁定/公告） |
| 编辑器 | ByteMD（Markdown） |
| 用户主页 | 头像 + 用户名 + 简介 + 发帖/回复数 |
| 通知 | 简单回复提醒 |
| 实施策略 | 渐进改造，复用 60-70% 现有代码 |

---

## 1. 数据库设计

### 1.1 表变更总览

| 现有表 | 变为 | 变更 |
|--------|------|------|
| `posts` | `topics` | 去 slug/summary/status/category_id，保留 id/title/content/author_id/created_at/updated_at，加 view_count |
| `tags` | 删除 | — |
| `post_tags` | 删除 | — |
| `comments` | 保留 | post_id → topic_id |
| `likes` | 保留 | post_id → topic_id |
| `users` | 扩展 | 加 topic_count, comment_count |
| — | `notifications` | 新表 |

### 1.2 topics

```sql
CREATE TABLE topics (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    content TEXT DEFAULT '',
    author_id INTEGER NOT NULL REFERENCES users(id),
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 1.3 notifications

```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    type VARCHAR NOT NULL,          -- 'reply'
    topic_id INTEGER REFERENCES topics(id),
    comment_id INTEGER REFERENCES comments(id),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 1.4 users (ALTER)

- `ADD topic_count INTEGER DEFAULT 0`
- `ADD comment_count INTEGER DEFAULT 0`

### 1.5 迁移要点

1. `posts` 表重命名为 `topics`，删除 slug/summary/status 列，添加 view_count
2. `comments.post_id` → `comments.topic_id`
3. `likes.post_id` → `likes.topic_id`
4. 删除 `tags`、`post_tags` 表
5. 新建 `notifications` 表
6. users 表添加 topic_count, comment_count

---

## 2. API 设计

### 2.1 帖子 (Topics)

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/api/topics` | 否 | 帖子列表 (?page=&size=&q=) |
| GET | `/api/topics/{id}` | 否 | 帖子详情 + 评论树 + 点赞信息 |
| POST | `/api/topics` | 是 | 发帖 (10/min 限流) |
| PUT | `/api/topics/{id}` | 是 | 编辑 (作者或管理员) |
| DELETE | `/api/topics/{id}` | 是 | 删除 (作者或管理员) |

### 2.2 评论 (Comments)

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/api/comments` | 是 | 发表评论 (10/min 限流)，触发通知 |
| DELETE | `/api/comments/{id}` | 是 | 删除 (作者或管理员) |

### 2.3 点赞 (Likes)

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/api/likes/{topic_id}` | 是 | 点赞 |
| DELETE | `/api/likes/{topic_id}` | 是 | 取消点赞 |

### 2.4 通知 (Notifications)

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/api/notifications` | 是 | 通知列表 (?page=&size=) |
| GET | `/api/notifications/unread-count` | 是 | 未读数量 |
| PUT | `/api/notifications/{id}/read` | 是 | 标记已读 |
| PUT | `/api/notifications/read-all` | 是 | 全部已读 |

### 2.5 认证 (Auth) — 不变

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| GET | `/api/auth/me` | 当前用户信息 |
| PUT | `/api/auth/me` | 更新个人资料 |
| PUT | `/api/auth/password` | 修改密码 |

### 2.6 用户 (Users)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/users/{username}` | 用户主页 (扩展 topic_count, comment_count) |

### 2.7 移除的路由

- `GET /api/tags` — 删除
- `GET/POST/PUT/DELETE /api/admin/posts/*` — 删除（/admin/posts 合并到 /api/topics）
- `GET /api/posts/{slug}` — 被 `/api/topics/{id}` 替代

---

## 3. 前端设计

### 3.1 路由变更

| 现有路由 | 新路由 | 视图 | 标题 |
|----------|--------|------|------|
| `/` | `/` | HomeView（重构为帖子列表） | 首页 |
| `/post/:slug` | `/topic/:id` | TopicDetailView | 帖子 |
| — | `/topic/new` | TopicEditView（新） | 发帖 |
| `/admin/posts/:id/edit` | `/topic/:id/edit` | TopicEditView | 编辑 |
| `/admin` | 删除 | — | — |
| `/admin/posts/new` | 删除 | — | — |
| `/login` | 保留 | LoginView | 登录 |
| `/register` | 保留 | RegisterView | 注册 |
| `/profile/edit` | 保留 | ProfileEditView | 编辑资料 |
| `/user/:username` | 扩展 | UserProfileView | 用户主页 |
| — | `/notifications` | NotificationsView（新） | 通知 |
| `/*` | 保留 | NotFoundView | 404 |

### 3.2 导航栏

```
新版: [Logo] 首页  搜索框  [发帖] [🔔+未读角标] [头像/登录]
旧版: [Logo] 首页  搜索框  [写文章] [后台] [登录/头像]
```

- "发帖"指向 `/topic/new`
- 通知铃铛显示未读数角标（轮询 `/api/notifications/unread-count`）
- 删除"后台"入口（管理功能分散到帖子旁的编辑/删除按钮）

### 3.3 视图变更要点

**HomeView** — 重构
- 去版块筛选，去标签筛选
- 纯帖子列表（分页 + 全文搜索）
- 每行: 标题 + 作者 + 回复数 + 点赞数 + 最后回复时间
- 骨架屏加载、空状态、错误重试保留

**TopicDetailView** — 改编自 PostDetailView
- 改用 id 获取数据（不再用 slug）
- Markdown 渲染 + 评论树 + 点赞
- 作者或管理员可见编辑/删除按钮

**TopicEditView** — 改编自 AdminPostEdit
- 新建/编辑模式共用
- ByteMD 编辑器保留
- 去掉 slug/summary/tags 字段，只保留 title + content
- 新建模式: POST /api/topics；编辑模式: PUT /api/topics/{id}

**UserProfileView** — 扩展
- 加 topic_count 和 comment_count 统计

**NotificationsView** — 新建
- 通知列表: 类型 + 关联帖子标题 + 时间 + 已读/未读状态
- 点击跳转到对应帖子的对应评论

### 3.4 复用组件

| 组件 | 状态 |
|------|------|
| AppToast | 直接复用 |
| ConfirmDialog | 直接复用 |
| BackToTop | 直接复用 |
| CommentItem | 直接复用（递归嵌套） |
| 主题系统 (26 CSS 变量) | 直接复用 |
| toast.js / confirm.js | 直接复用 |
| auth store (Pinia) | 直接复用 |
| api/client.js (Axios) | 直接复用 |

### 3.5 删除的视图

- `AdminDashboard.vue` — 不再需要个人文章管理页
- `AdminPostEdit.vue` — 被 TopicEditView 替代

---

## 4. 通知触发逻辑

- 评论帖子时：通知帖子作者（自己回复自己除外）
- 回复评论时：通知被回复的评论作者（自己回复自己除外）
- 前端轮询 `/api/notifications/unread-count` 更新导航栏角标（间隔 30s）

---

## 5. 实施策略

渐进改造，保持项目始终可运行。建议分阶段：

1. **数据库迁移** — 执行 SQL 变更（改表结构）
2. **后端 models/schemas** — 重命名模型，删除废弃字段
3. **后端 crud** — 函数重命名 + 通知 CRUD
4. **后端 main.py** — 路由更新
5. **前端路由** — 更新 router
6. **前端视图** — 逐个适配/新建
7. **验证** — 逐功能验收

---

## 6. 不变项

以下基础设施不变：

- JWT 认证机制
- bcrypt 密码哈希
- CORS / 限流 / 日志中间件
- bleach HTML 清理
- 暗色/亮色主题系统
- Pinia 状态管理
- Axios 拦截器
- Toast/Confirm composable
