# Iter-1 Opportunity Engine Alignment Result

- 时间字段：字段集采用 start/end/deadline + time_status + timeliness_level；机会内容优先看 deadline，再看 event_end
- 参与状态：participation_status 成为正式字段；主列表优先 participable，灰区降权，非参与默认不占主位
- 排序策略：正式落 ranking_score 字段；participation 第一，time/urgency 第二
- 存储策略：正式采用 raw + normalized + projection 三层；主列表依赖摘要，原文与快照只做引用和兜底

## Extra Notes
raw + normalized + projection
这是啥意思？为什么搞三个字段，这一点不理解