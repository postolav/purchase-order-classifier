"""Load the curated KPMG taxonomy."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml


@dataclass
class Category:
    name: str
    weight: float
    include: List[str]


@dataclass
class Taxonomy:
    categories: List[Category]
    exclude_keywords: List[str]
    exclude_override_floor: float

    def summary(self) -> str:
        """A compact text description for the LLM prompt."""
        lines = ["KPMG service categories (comparable = keep):"]
        for c in self.categories:
            lines.append(f"- {c.name}: e.g. {', '.join(c.include[:5])}")
        lines.append(
            "Clearly NOT comparable (discard): "
            + ", ".join(self.exclude_keywords[:20])
            + ", ..."
        )
        return "\n".join(lines)


def load_taxonomy(path: str | Path) -> Taxonomy:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    categories = [
        Category(name=c["name"], weight=float(c["weight"]), include=list(c["include"]))
        for c in data["categories"]
    ]
    exc = data.get("excludes", {})
    return Taxonomy(
        categories=categories,
        exclude_keywords=[k.lower() for k in exc.get("keywords", [])],
        exclude_override_floor=float(exc.get("override_floor", 0.9)),
    )
