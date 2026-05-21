# iter-1: 交付标准

> 历史参考文档。这里只覆盖了早期 content filtering 子问题，当前有效的 iter-1 验收口径请以 `docs/backend-rebuild/iter-1-prd.md` 为准。

## 交付清单

### 1. 数据库

- [ ] Article 表包含 `content_type` 字段（String(20)，默认 "unknown"）
- [ ] Article 表包含 `display_level` 字段（String(10)，默认 "low"）
- [ ] 已有数据重新同步后，所有文章都有正确的 content_type 值

### 2. API

- [ ] `GET /api/articles` 默认不返回 `display_level=hidden` 的文章
- [ ] `GET /api/articles?content_type=actionable` 只返回 actionable 文章
- [ ] `GET /api/articles?show_all=true` 返回全部文章（含 hidden）
- [ ] `GET /api/articles?content_type=actionable&category=activity` 组合过滤正常
- [ ] `GET /api/categories` 响应包含 `content_type_stats` 字段
- [ ] `POST /api/sync` 同步后新文章自动有 content_type 和 display_level

### 3. 前端

- [ ] 首页默认只显示 actionable 内容
- [ ] 有"显示全部" / "仅可参与"切换按钮
- [ ] 切换按钮功能正常（切换后重新加载对应数据）
- [ ] 文章卡片显示 content_type 中文标签（可参与 / 参考）

### 4. 无回归

- [ ] 原有分类筛选功能不受影响
- [ ] 原有搜索功能不受影响
- [ ] 原有分页功能不受影响
- [ ] 原有文章详情功能不受影响
- [ ] 原有手动同步功能不受影响

### 5. 分类质量

- [ ] 抽样 10 篇文章，content_type 判断准确率 >= 80%
- [ ] 无明显的 actionable / non_actionable 误判（如活动总结标为 actionable）

---

## 不在本迭代范围

- 管理页人工修正 content_type
- display_level 独立设置
- LLM 辅助分类
- 前端来源库 / 管理页
