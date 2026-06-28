from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class UniverseMember:
    symbol: str
    name: str
    exchange: str
    asset_type: str
    currency: str
    provider_symbol: str
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class UniverseSummary:
    universe_id: str
    name: str
    description: str
    market: str
    asset_type: str
    source: str
    source_url: str
    member_count: int
    refreshed_at: datetime


@dataclass(frozen=True, slots=True)
class UniverseDetail:
    summary: UniverseSummary
    members: tuple[UniverseMember, ...]


@dataclass(frozen=True, slots=True)
class UniverseRefreshResult:
    summary: UniverseSummary
    inserted_symbols: int
    members: tuple[UniverseMember, ...]
