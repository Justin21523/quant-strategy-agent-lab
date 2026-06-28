from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class ResearchPreset:
    preset_id: str
    name: str
    description: str
    config: dict[str, Any]
    created_at: datetime
