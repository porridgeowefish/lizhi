# iter-1: content_type + display_level 内容过滤

> 历史参考文档。该文件只记录了 iter-1 早期的内容过滤切片，不再代表当前完整 iter-1 目标。当前正式 PRD 请优先阅读 `docs/backend-rebuild/iter-1-prd.md`。

## 设计文档

> PRD v0.11 核心机制：荔知不是公众号阅读器，而是活动机会发现平台。本迭代实现内容类型判断，让首页优先展示"可参与信息"。

---

## 1. 数据库变更

### 1.1 Article 模型新增字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| content_type | String(20) | `"unknown"` | `actionable` / `reference` / `non_actionable` / `unknown` |
| display_level | String(10) | `"low"` | `normal` / `low` / `hidden` |

### 1.2 display_level 推导规则

由 content_type 自动推导，不独立设置：

| content_type | display_level | 说明 |
|--------------|---------------|------|
| actionable | normal | 首页正常展示 |
| reference | low | 降权展示，可切换查看 |
| non_actionable | hidden | 默认不进入首页 |
| unknown | low | 降权展示 |

### 1.3 已有数据处理

新增字段后，对已有数据：
- 通过 `POST /api/sync` 重新同步并补齐 `content_type` 与 `display_level`
- 不额外维护独立脚本，以统一同步链路作为唯一更新入口

---

## 2. 分类引擎

### 2.1 关键词规则

```python
CONTENT_TYPE_RULES = {
    "actionable": [
        "报名", "招募", "招新", "征集", "预告", "开始",
        "申请", "征稿", "志愿者", "宣讲会", "讲座预告",
        "活动预告", "报名通道", "截止", "通知"
    ],
    "non_actionable": [
        "回顾", "总结", "圆满结束", "顺利举办", "精彩回顾",
        "活动纪实", "风采展示", "获奖名单", "喜报", "成果展示",
        "会议新闻", "表彰"
    ],
    "reference": [
        "攻略", "指南", "合集", "清单", "一览", "活动日历", "须知"
    ]
}
```

### 2.2 匹配逻辑

```python
def classify_content_type(title: str, description: str = "") -> str:
    text = f"{title} {description}"
    # 优先级: non_actionable > actionable > reference
    for ct in ["non_actionable", "actionable", "reference"]:
        for kw in CONTENT_TYPE_RULES[ct]:
            if kw in text:
                return ct
    return "non_actionable"  # 默认宁缺勿滥
```

关键设计：
- **non_actionable 优先**: "活动回顾"不会被"报名"误判为 actionable
- **默认 non_actionable**: 未匹配的内容不进入首页，宁缺勿滥

### 2.3 display_level 推导函数

```python
DISPLAY_LEVEL_MAP = {
    "actionable": "normal",
    "reference": "low",
    "non_actionable": "hidden",
}

def get_display_level(content_type: str) -> str:
    return DISPLAY_LEVEL_MAP.get(content_type, "low")
```

---

## 3. API 变更

### 3.1 GET /api/articles 新增参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| content_type | string | null | 过滤内容类型: `actionable` / `reference` / `non_actionable` |
| show_all | bool | false | `true` 时忽略 display_level 过滤，返回全部文章 |

**过滤逻辑：**
- `show_all=false`（默认）: 只返回 `display_level != "hidden"` 的文章
- `show_all=true`: 返回全部文章（含 hidden）
- `content_type` 有值时: 按指定 content_type 过滤

**组合示例：**
- `GET /api/articles` → 非 hidden 的文章
- `GET /api/articles?content_type=actionable` → 只返回 actionable
- `GET /api/articles?show_all=true` → 全部文章（含 hidden）
- `GET /api/articles?category=activity&content_type=actionable` → activity 分类下的 actionable 文章

### 3.2 GET /api/articles/categories 新增返回

在现有分类统计基础上，新增 `content_type_stats` 字段：

```json
{
  "categories": [
    {"category": "activity", "count": 15},
    {"category": "lecture", "count": 8}
  ],
  "content_type_stats": {
    "actionable": 30,
    "reference": 5,
    "non_actionable": 15,
    "unknown": 4
  }
}
```

### 3.3 响应模型变更

`ArticleOut` 新增字段：
- `content_type: str` — 内容类型
- `display_level: str` — 展示等级

---

## 4. 同步流程变更

### 4.1 main.py sync_all 改动

在现有 `classify()` 调用后，增加 content_type 计算：

```python
from services.classifier import classify, classify_content_type, get_display_level

# 现有代码
categories = classify(ra.get("title", ""), ra.get("description", ""))

# 新增
content_type = classify_content_type(ra.get("title", ""), ra.get("description", ""))
display_level = get_display_level(content_type)

# Article 创建时加入新字段
article = Article(
    ...,
    categories=",".join(categories),
    content_type=content_type,
    display_level=display_level,
)
```

---

## 5. 前端变更

### 5.1 api.js 变更

`getArticles` 增加 `content_type` 和 `show_all` 参数：

```javascript
export const getArticles = (params) => api.get('/articles', { params }).then(r => r.data)
// params 可包含: { category, search, mp_name, offset, limit, content_type, show_all }
```

### 5.2 App.vue 变更

- **默认加载**: `getArticles({ content_type: 'actionable' })`
- **切换按钮**: "仅可参与" / "显示全部"
  - 切换到"显示全部": `getArticles({ show_all: true })`
  - 切换回"仅可参与": `getArticles({ content_type: 'actionable' })`
- **卡片标签**: 显示 content_type 对应的中文标签
  - actionable → "可参与"
  - reference → "参考"
  - non_actionable → 不在首页显示
- **搜索时**: 搜索结果不受 content_type 过滤，使用 `show_all: true`

---

## 6. 涉及文件清单

| 文件 | 改动类型 | 改动说明 |
|------|----------|----------|
| `backend/models.py` | 修改 | Article 新增 content_type + display_level 字段 |
| `backend/schemas.py` | 修改 | ArticleOut 新增 2 个字段 |
| `backend/services/classifier.py` | 修改 | 新增 classify_content_type() + get_display_level() |
| `backend/config.py` | 修改 | 新增 CONTENT_TYPE_RULES 配置 |
| `backend/routers/articles.py` | 修改 | 新增查询参数，过滤逻辑 |
| `backend/main.py` | 修改 | sync_all 中调用新分类函数 |
| `frontend/src/api.js` | 修改 | 参数透传（无需改动函数签名） |
| `frontend/src/App.vue` | 修改 | 切换按钮 + 标签显示 |
