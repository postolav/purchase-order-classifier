"""Anthropic client wrapper: structured scoring, optional web search, disk cache.

Caches by a hash of (supplier, category, model, web_search) so identical lines and
repeat runs are cheap and reproducible. The cache is a plain JSON file.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, Optional

# The JSON schema the model must return for each line.
_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "similarity": {"type": "number"},
        "confidence": {"type": "number"},
        "kpmg_category": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["similarity", "confidence", "kpmg_category", "reason"],
    "additionalProperties": False,
}


def _clamp01(x) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, v))


class LLMScorer:
    def __init__(
        self,
        taxonomy_summary: str,
        model: str,
        websearch_model: str,
        cache_dir: str = "cache",
        web_search: bool = True,
    ):
        self.taxonomy_summary = taxonomy_summary
        self.model = model
        self.websearch_model = websearch_model
        self.web_search = web_search
        self.cache_path = Path(cache_dir) / "llm_scores.json"
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, dict] = {}
        if self.cache_path.exists():
            try:
                self._cache = json.loads(self.cache_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self._cache = {}
        self._client = None  # lazy — only constructed when a real call is needed

    # -- caching ---------------------------------------------------------------
    def _key(self, supplier: str, category: str, use_web: bool) -> str:
        raw = f"{self.model}|{use_web}|{supplier.strip().lower()}|{category.strip().lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _save_cache(self) -> None:
        self.cache_path.write_text(
            json.dumps(self._cache, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # -- anthropic -------------------------------------------------------------
    def _get_client(self):
        if self._client is None:
            import anthropic  # imported lazily so offline/rule-only runs need no SDK

            self._client = anthropic.Anthropic()
        return self._client

    def _prompt(self, supplier: str, category: str, amount_eur, tentative: Optional[str]) -> str:
        return (
            f"{self.taxonomy_summary}\n\n"
            "Assess whether this Irish Department of Defence purchase-order line is for a "
            "service comparable to KPMG's offering. Return JSON with:\n"
            "- similarity: 0..1 (how close to a KPMG-comparable professional service)\n"
            "- confidence: 0..1 (how sure you are)\n"
            "- kpmg_category: the closest KPMG category name, or 'None'\n"
            "- reason: one short sentence.\n\n"
            f"Supplier: {supplier}\n"
            f"Raw category/description: {category}\n"
            f"Amount (EUR): {amount_eur}\n"
            f"Rule-based tentative match: {tentative or 'None'}\n"
        )

    def score(
        self,
        supplier: str,
        category: str,
        amount_eur,
        tentative: Optional[str],
        use_web: bool = False,
    ) -> dict:
        """Return {similarity, confidence, kpmg_category, reason, source_stage}."""
        use_web = bool(use_web and self.web_search)
        key = self._key(supplier, category, use_web)
        if key in self._cache:
            return self._cache[key]

        client = self._get_client()
        model = self.websearch_model if use_web else self.model
        tools = (
            [{"type": "web_search_20260209", "name": "web_search", "max_uses": 3}]
            if use_web
            else []
        )
        kwargs = dict(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": self._prompt(supplier, category, amount_eur, tentative)}],
        )
        if tools:
            # With web search we can't also constrain output_config.format reliably,
            # so ask for a fenced JSON object and parse it out.
            kwargs["tools"] = tools
            kwargs["messages"][0]["content"] += (
                "\n\nAfter any research, respond with ONLY a JSON object matching the "
                "fields above."
            )
        else:
            kwargs["output_config"] = {"format": {"type": "json_schema", "schema": _OUTPUT_SCHEMA}}

        resp = client.messages.create(**kwargs)
        text = next((b.text for b in resp.content if getattr(b, "type", None) == "text"), "")
        parsed = _extract_json(text)

        result = {
            "similarity": _clamp01(parsed.get("similarity")),
            "confidence": _clamp01(parsed.get("confidence")),
            "kpmg_category": (parsed.get("kpmg_category") or None) if parsed.get("kpmg_category") not in (None, "None") else None,
            "reason": str(parsed.get("reason", ""))[:300],
            "source_stage": "llm+web" if use_web else "llm",
        }
        self._cache[key] = result
        self._save_cache()
        return result


def _extract_json(text: str) -> dict:
    """Best-effort parse of a JSON object from the model's text."""
    text = text.strip()
    if not text:
        return {}
    # Strip markdown fences if present.
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}
