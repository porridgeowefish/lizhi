# Reuse Decision Table

> 这份表用于把“可以借鉴，但不能照搬”落成明确执行口径。

| Existing Asset | Current Role | Decision | New Form |
| --- | --- | --- | --- |
| `GET /api/articles` | 文章列表查询 | 保留接口形状，升级响应契约与搜索语义 | `GET /api/articles` 返回 `items + total + offset + limit` |
| `GET /api/articles/{id}` | 文章详情 | 保留 | 增加显式 `404` 契约与结构化分类 |
| `GET /api/articles/categories` | 分类统计 | 保留 | 增加 `content_type_stats` |
| `GET /api/feeds` | 来源列表 | 不直接保留命名 | 更名为 `GET /api/sources` |
| `POST /api/sync` | 手动同步 | 保留接口职责，重做实现 | 返回 `job_id` 和任务状态摘要 |
| `feeds` table | 来源简表 | 不照搬 | 重构为 `sources` |
| `articles` table | 文章投影表 | 部分借鉴字段语义 | 重构为结构化 `articles` |
| `wress_id` | 上游文章标识 | 不保留命名 | `upstream_article_id` |
| `mp_id` | 上游来源标识 | 不保留命名 | `upstream_source_id` |
| `mp_name` | 来源名称 | 不保留命名 | `source_name` / `name` |
| `services/fetcher.py` | 上游 API 适配器 | 只借鉴模式 | 新版 adapter 重新实现 |
| `services/classifier.py` | 关键词分类 | 只借鉴规则方向 | 新版分类服务重新实现 |
| `categories` 逗号字符串 | 分类结果存储 | 不保留 | `article_categories` 关系表 |
| `content_html` | 正文快照 | 保留概念 | 分离原始内容与规范化内容策略 |
| APScheduler 定时同步 | 周期性同步机制 | 保留能力边界 | 新版调度器接入同步任务模型 |
| WeRSS `db.db` | 上游完整运行库 | 不接入本地领域建模 | 仅通过 connector 消费 |
| `data/cache/content/*.json` | 上游正文缓存 | 只作为现状参考 | 不作为新系统正式存储契约 |

