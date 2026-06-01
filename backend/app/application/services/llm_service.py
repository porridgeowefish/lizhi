from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx

from app.application.classification import parse_llm_payload
from app.core.config import Settings
from app.domain.enums import LlmStatus


class LlmService:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def enabled(self) -> bool:
        return bool(
            self.settings.llm_enabled
            and self.settings.llm_base_url
            and self.settings.llm_api_key
            and self.settings.llm_model
        )

    async def summarize_and_extract(self, *, title: str, summary: str, content_text: str) -> dict:
        if not self.enabled:
            return {
                "summary": "",
                "structured": {},
                "status": LlmStatus.NOT_REQUESTED.value,
                "model": "",
                "processed_at": None,
            }

        prompt = (
            "你是校园机会内容抽取助手。"
            "请只输出 JSON，对以下文章生成简短标题和摘要，并抽取候选结构化字段。"
            "不要做最终业务判断，不要输出解释。"
            'JSON 字段固定为: title,summary,category,is_opportunity,is_recap,event_type,audience,call_to_action,'
            "deadline_text,start_time_text,end_time_text,key_evidence,"
            "deadline_iso,start_iso,end_iso。"
            "title 字段必须：20字以内，突出活动核心信息（做什么+关键限定），去掉组织方前缀和宣传语气词，"
            "使用简洁直白的表达，不要用引号、括号或特殊符号。"
            "category 字段必须从以下选项中选择一个最匹配的："
            "campus_activity（校园活动/社团/迎新/文体娱乐/学生组织活动），"
            "competition（学科竞赛/比赛/大赛/作品征集/项目申报），"
            "volunteer（志愿公益/公益服务/志愿招募），"
            "exam_certification（考试考证/四六级/普通话/计算机等级考试/教师资格证/法考/软考/CFA），"
            "recruitment（就业招聘/校招/实习/企业宣讲会/岗位投递），"
            "lecture（讲座论坛/知识分享/学术交流/研讨会），"
            "graduate_study（升学留学/考研/保研/研究生招生/交换项目），"
            "other（无法归入以上机会分类）。"
            "若多个分类都匹配，按上述顺序优先选择靠前分类。"
            "判断 category 时按两步进行：第一步优先根据 title 和 summary 判断一级分类，"
            "第二步再用 content_text 辅助确认、纠错和补充细节；"
            "如果标题和正文冲突，除非正文出现明确排除或更具体证据，否则以标题/摘要为准。"
            "如果无法判断类别，填 other。"
            "summary 字段控制在200字以内，只提取关键信息（活动内容、时间、地点、参与方式），不要复述原文。"
            "deadline_iso/start_iso/end_iso 为 ISO 8601 日期时间字符串（如 2025-06-15T14:00:00），"
            "无法识别则填 null。"
        )
        user_input = json.dumps(
            {
                "title": title,
                "summary": summary,
                "content_text": content_text[: self.settings.llm_max_input_chars],
            },
            ensure_ascii=False,
        )
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_input},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(base_url=self.settings.llm_base_url, timeout=self.settings.llm_timeout_seconds) as client:
            response = await client.post("/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        content = ""
        choices = data.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}
            content = message.get("content") or ""
        structured = parse_llm_payload(content)
        return {
            "summary": str(structured.get("summary") or ""),
            "structured": structured,
            "status": LlmStatus.COMPLETED.value if structured else LlmStatus.FAILED.value,
            "model": self.settings.llm_model,
            "processed_at": datetime.now(timezone.utc),
        }
