# Rebuild Constraints

## 1. We Can Reuse

### Reusable Boundaries

- 聚合型产品 API 入口形状
- 上游适配器思想
- `Source -> Article` 的核心对象边界
- 规则优先的轻量分类策略
- 定时同步 + 手动同步的基本工作流

### Reusable Contract Semantics

- 上游来源稳定标识
- 上游文章稳定标识
- `original_url`
- `cover_url`
- `published_at`
- `summary`
- `content_html` 作为可选快照

### Reusable State Dimensions

- 来源启用状态
- 抓取任务状态
- 内容可用状态

## 2. We Must Not Copy

### Do Not Copy the Current Internal Model

- WeRSS 表结构
- `cascade_*`
- `users`
- `access_keys`
- `message_tasks`
- `filter_rules`

### Do Not Copy Current Naming

- `wress_id`
- `mp_id`
- `mp_name`
- `faker_id`
- `werss:*`

### Do Not Copy Current Implementation Shortcuts

- `categories` 逗号字符串
- 明文账号密码配置
- 只拉 `limit=50` 的同步策略
- router 直连 ORM 的查询结构
- 上游 HTML 直接作为唯一正文标准

## 3. New Naming Direction

- `feeds` -> `sources`
- `wress_id` -> `upstream_article_id`
- `mp_id` -> `upstream_source_id`
- `mp_name` -> `source_name`
- `sync_all()` -> `sync_sources()` 或 `run_ingestion_job()`

## 4. Rebuild Boundary

第一阶段重构只聚焦后端，不处理前端重建。

### In Scope

- 来源域模型
- 内容同步链路
- 内容分类链路
- 查询 API
- 任务日志
- 测试骨架

### Out of Scope

- 多高校扩展
- 社交化功能
- 推荐流
- 评论
- 用户运营后台
- 上游 WeRSS 平台能力复制
