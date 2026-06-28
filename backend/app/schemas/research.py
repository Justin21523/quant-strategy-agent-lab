from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.market import ProviderSelection
from app.domain.portfolio import RebalanceFrequency
from app.domain.scanner import SortDirection
from app.schemas.quality import DataQualityGateRequest
from app.schemas.scans import ScannerRulesRequest


class ResearchScannerConfigRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preset_id: str = "trend_momentum"
    rules: ScannerRulesRequest | None = Field(
        default_factory=lambda: ScannerRulesRequest(
            enable_close_above_sma_200=False,
            enable_sma_20_above_sma_60=False,
            enable_rsi_range=False,
            enable_volume_ratio_20d=False,
            enable_return_60d=False,
            rsi_min=0,
            rsi_max=100,
            volume_ratio_20d_min=0,
            return_60d_min_pct=-100,
        )
    )
    sort_key: str = "return_60d_pct"
    sort_direction: SortDirection = SortDirection.DESC
    result_limit: int = Field(default=20, ge=1, le=200)


class ResearchPortfolioMatrixConfigRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    scanner_preset_id: str = "trend_momentum"
    frequency: RebalanceFrequency = RebalanceFrequency.MONTHLY
    top_n: int = Field(default=8, ge=1, le=100)
    lookback_days: int = Field(default=365, ge=30, le=1500)
    start: date | None = None
    end: date | None = None


class ResearchStrategyMatrixConfigRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    template_id: str = "buy_and_hold"
    parameters: dict[str, Any] = Field(default_factory=dict)
    top_n: int = Field(default=6, ge=1, le=100)
    start: date | None = None
    end: date | None = None


class ResearchPipelineRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_label: str = "Demo Quick Research"
    universe_id: str = "demo_research_sample"
    start: date = date(2023, 1, 3)
    end: date = date(2025, 12, 31)
    provider: ProviderSelection = ProviderSelection.CSV
    sync_mode: str = "all"
    sync_chunk_size: int = Field(default=25, ge=1, le=100)
    allow_fallback: bool = False
    stale_after: date | None = None
    benchmark_symbol: str = "SPY"
    initial_cash: float = Field(default=100_000.0, gt=0)
    commission: float = Field(default=0.001, ge=0)
    slippage: float = Field(default=0.0005, ge=0)
    quality_gate: DataQualityGateRequest = Field(
        default_factory=lambda: DataQualityGateRequest(
            min_bars=200,
            allow_fixture_data=True,
            max_missing_weekdays=1000,
        )
    )
    scanner_config: ResearchScannerConfigRequest = Field(
        default_factory=ResearchScannerConfigRequest
    )
    portfolio_matrix_configs: list[ResearchPortfolioMatrixConfigRequest] = Field(
        default_factory=lambda: [
            ResearchPortfolioMatrixConfigRequest(
                label="Trend Momentum Monthly Top 8",
                scanner_preset_id="trend_momentum",
                frequency=RebalanceFrequency.MONTHLY,
                top_n=8,
                end=date(2023, 9, 29),
            ),
            ResearchPortfolioMatrixConfigRequest(
                label="Low Volatility Monthly Top 10",
                scanner_preset_id="low_volatility_trend",
                frequency=RebalanceFrequency.MONTHLY,
                top_n=10,
                end=date(2023, 9, 29),
            ),
            ResearchPortfolioMatrixConfigRequest(
                label="Oversold Weekly Top 5",
                scanner_preset_id="oversold_watchlist",
                frequency=RebalanceFrequency.WEEKLY,
                top_n=5,
                end=date(2023, 9, 29),
            ),
        ]
    )
    strategy_matrix_configs: list[ResearchStrategyMatrixConfigRequest] = Field(
        default_factory=lambda: [
            ResearchStrategyMatrixConfigRequest(
                template_id="buy_and_hold",
                top_n=6,
                end=date(2023, 9, 29),
            ),
            ResearchStrategyMatrixConfigRequest(
                template_id="ma_crossover",
                top_n=6,
                end=date(2023, 9, 29),
            ),
            ResearchStrategyMatrixConfigRequest(
                template_id="macd_trend_following",
                top_n=6,
                end=date(2023, 9, 29),
            ),
        ]
    )

    @model_validator(mode="after")
    def validate_dates(self) -> ResearchPipelineRunRequest:
        if self.start > self.end:
            raise ValueError("start must be on or before end")
        return self


class ResearchRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: dict[str, Any]


class ResearchRunListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0)
    runs: list[dict[str, Any]]


class ResearchPresetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preset_id: str
    name: str
    description: str
    config: ResearchPipelineRunRequest


class ResearchPresetResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preset_id: str
    name: str
    description: str
    config: dict[str, Any]
    created_at: datetime


class ResearchPresetListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0)
    presets: list[ResearchPresetResponse]
