"""
Разбор свободного текстового описания навыков пользователя через Anthropic Claude.

MCP используется как канал самого приложения к LLM: если в settings.MCP_SERVER_URLS
заданы адреса MCP-серверов, они передаются в Anthropic Messages API (`mcp_servers`),
и модель может вызывать их инструменты при разборе текста. Без ключа Anthropic
(ANTHROPIC_API_KEY не задан) используется офлайн-эвристика, чтобы функциональность
оставалась доступной без внешних сервисов.
"""

import re
from typing import Any, Dict, List, Optional

from django.conf import settings

from core.constants import SKILL_LEVELS

_EXTRACT_SKILLS_TOOL = {
    "name": "extract_skills",
    "description": "Извлекает список навыков программиста и оценённый уровень владения каждым из текста.",
    "input_schema": {
        "type": "object",
        "properties": {
            "skills": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Название навыка (например, Python, Django, SQL)"},
                        "level": {"type": "string", "enum": list(SKILL_LEVELS)},
                    },
                    "required": ["name", "level"],
                },
            }
        },
        "required": ["skills"],
    },
}

_ADVANCED_HINTS = ("эксперт", "продвинут", "профессионал", "опытн", "senior", "advanced", "expert")
_BEGINNER_HINTS = ("начина", "изуча", "основ", "junior", "beginner", "новичок")
_INTERMEDIATE_HINTS = ("средн", "уверенн", "intermediate", "практическ")


class SkillTextAnalyzer:
    def __init__(self, client: Optional[Any] = None) -> None:
        self.client = client if client is not None else self._build_client()

    def _build_client(self) -> Optional[Any]:
        if not settings.ANTHROPIC_API_KEY:
            return None
        import anthropic

        return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def analyze(self, text: str) -> List[Dict[str, str]]:
        """Возвращает список {"name": ..., "level": ...}, извлечённых из текста."""
        if not text or not text.strip():
            return []
        if self.client is None:
            return self._fallback_analyze(text)
        return self._analyze_with_llm(text)

    def _analyze_with_llm(self, text: str) -> List[Dict[str, str]]:
        request_kwargs: Dict[str, Any] = {
            "model": settings.ANTHROPIC_MODEL,
            "max_tokens": 1024,
            "tools": [_EXTRACT_SKILLS_TOOL],
            "tool_choice": {"type": "tool", "name": "extract_skills"},
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Извлеки из текста навыки программиста и оцени уровень владения каждым "
                        f"(beginner/intermediate/advanced/expert):\n\n{text}"
                    ),
                }
            ],
        }
        if settings.MCP_SERVER_URLS:
            request_kwargs["extra_headers"] = {"anthropic-beta": "mcp-client-2025-04-04"}
            request_kwargs["mcp_servers"] = [
                {"type": "url", "url": url, "name": f"mcp-server-{i}"}
                for i, url in enumerate(settings.MCP_SERVER_URLS)
            ]

        message = self.client.messages.create(**request_kwargs)
        for block in message.content:
            if getattr(block, "type", None) == "tool_use":
                skills = block.input.get("skills", [])
                return [s for s in skills if s.get("name")]
        return []

    def _fallback_analyze(self, text: str) -> List[Dict[str, str]]:
        """Простая эвристика без обращения к LLM (используется, если ключ не задан)."""
        chunks = re.split(r"[,\n;.]+", text)
        results = []
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            lowered = chunk.lower()
            level = "beginner"
            if any(hint in lowered for hint in _ADVANCED_HINTS):
                level = "advanced"
            elif any(hint in lowered for hint in _INTERMEDIATE_HINTS):
                level = "intermediate"
            elif any(hint in lowered for hint in _BEGINNER_HINTS):
                level = "beginner"
            name = re.sub(
                r"\b(" + "|".join(_ADVANCED_HINTS + _BEGINNER_HINTS + _INTERMEDIATE_HINTS) + r")\w*\b",
                "",
                chunk,
                flags=re.IGNORECASE,
            ).strip(" -:")
            if name:
                results.append({"name": name, "level": level})
        return results
