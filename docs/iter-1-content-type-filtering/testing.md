# iter-1: 测试标准

> 历史参考文档。该文件早于当前“规则优先机会引擎”PRD，只能作为旧测试背景，不再是现行测试合同。

## 1. 单元测试（后端）

### 1.1 classify_content_type 函数

| # | 测试用例 | 输入 | 预期输出 |
|---|----------|------|----------|
| 1 | actionable - 报名 | title="讲座报名通知" | "actionable" |
| 2 | actionable - 招募 | title="志愿者招募" | "actionable" |
| 3 | actionable - 预告 | title="讲座预告" | "actionable" |
| 4 | actionable - 截止 | title="报名截止提醒" | "actionable" |
| 5 | non_actionable - 回顾 | title="活动回顾" | "non_actionable" |
| 6 | non_actionable - 喜报 | title="获奖喜报" | "non_actionable" |
| 7 | non_actionable - 总结 | title="活动总结" | "non_actionable" |
| 8 | reference - 攻略 | title="保研攻略" | "reference" |
| 9 | reference - 指南 | title="选课指南" | "reference" |
| 10 | 无匹配默认 | title="深圳大学食堂新菜单" | "non_actionable" |
| 11 | 优先级: non_actionable > actionable | title="活动回顾与报名" | "non_actionable" |
| 12 | description 参与匹配 | title="xxx", description="招募志愿者" | "actionable" |

### 1.2 get_display_level 函数

| # | content_type | 预期 display_level |
|---|--------------|-------------------|
| 1 | actionable | normal |
| 2 | reference | low |
| 3 | non_actionable | hidden |
| 4 | unknown | low |
| 5 | (任意其他) | low |

---

## 2. API 集成测试

| # | 测试场景 | 请求 | 预期结果 |
|---|----------|------|----------|
| 1 | 默认列表 | `GET /api/articles` | 不含 display_level=hidden 的文章 |
| 2 | 过滤 actionable | `GET /api/articles?content_type=actionable` | 只返回 actionable 文章 |
| 3 | 过滤 non_actionable | `GET /api/articles?content_type=non_actionable` | 只返回 non_actionable 文章 |
| 4 | 显示全部 | `GET /api/articles?show_all=true` | 返回全部文章（含 hidden） |
| 5 | 组合过滤 | `GET /api/articles?category=activity&content_type=actionable` | 同时满足两个条件 |
| 6 | 分类统计 | `GET /api/categories` | 响应含 content_type_stats 字段 |
| 7 | 同步后验证 | `POST /api/sync` → `GET /api/articles` | 新文章有 content_type 字段 |
| 8 | 文章详情 | `GET /api/articles/{id}` | 返回含 content_type + display_level |

---

## 3. 前端手动测试

| # | 测试场景 | 操作 | 预期结果 |
|---|----------|------|----------|
| 1 | 首页默认加载 | 打开首页 | 只显示 actionable 文章 |
| 2 | 切换显示全部 | 点击"显示全部" | 显示所有文章（含 non_actionable） |
| 3 | 切换回仅可参与 | 点击"仅可参与" | 回到只显示 actionable |
| 4 | 分类+过滤 | 选"活动"分类 + "仅可参与" | 只显示活动类 actionable 文章 |
| 5 | 搜索不受限 | 搜索"回顾" | 能搜到 non_actionable 文章 |
| 6 | 文章卡片标签 | 查看卡片 | actionable 文章显示"可参与"标签 |
| 7 | 原有功能回归 | 翻页、详情、同步 | 功能正常无报错 |

---

## 4. 分类质量抽检

从当前 54 篇文章中抽样 10 篇，人工验证 content_type 判断是否正确。

| # | 文章标题 | 预期 content_type | 实际 content_type | 是否正确 |
|---|----------|-------------------|-------------------|----------|
| 1 | （同步后填写） | | | |
| 2 | | | | |
| 3 | | | | |
| ... | | | | |

通过标准: 10 篇中 >= 8 篇判断正确（准确率 >= 80%）。
