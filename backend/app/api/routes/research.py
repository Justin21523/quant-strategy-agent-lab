from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.api.dependencies import get_research_pipeline_service
from app.domain.errors import ResearchPresetNotFoundError, ResearchRunNotFoundError
from app.domain.research import ResearchPreset
from app.schemas.research import (
    ResearchPresetListResponse,
    ResearchPresetRequest,
    ResearchPresetResponse,
    ResearchRunListResponse,
    ResearchRunResponse,
)
from app.services.research_pipeline_service import ResearchPipelineService

router = APIRouter(prefix="/research", tags=["research pipelines"])
ResearchPipelineServiceDependency = Annotated[
    ResearchPipelineService, Depends(get_research_pipeline_service)
]


@router.get(
    "/runs/latest",
    response_model=ResearchRunResponse,
    summary="Read the latest research pipeline summary",
)
def latest_research_run(
    service: ResearchPipelineServiceDependency,
) -> ResearchRunResponse:
    summary = service.latest_summary()
    if summary is None:
        raise ResearchRunNotFoundError(
            "No completed research pipeline runs are available.", details={}
        )
    return ResearchRunResponse(summary=summary)


@router.get(
    "/runs",
    response_model=ResearchRunListResponse,
    summary="List recent research pipeline summaries",
)
def list_research_runs(
    service: ResearchPipelineServiceDependency,
    limit: int = 20,
) -> ResearchRunListResponse:
    runs = service.list_summaries(limit=limit)
    return ResearchRunListResponse(total=len(runs), runs=runs)


@router.get(
    "/runs/{run_id}",
    response_model=ResearchRunResponse,
    summary="Read one research pipeline summary",
)
def get_research_run(
    run_id: str,
    service: ResearchPipelineServiceDependency,
) -> ResearchRunResponse:
    summary = service.get_summary(run_id)
    if summary is None:
        raise ResearchRunNotFoundError(
            f"Unknown research pipeline run: {run_id}",
            details={"run_id": run_id},
        )
    return ResearchRunResponse(summary=summary)


@router.get(
    "/presets",
    response_model=ResearchPresetListResponse,
    summary="List research pipeline presets",
)
def list_research_presets(
    service: ResearchPipelineServiceDependency,
) -> ResearchPresetListResponse:
    presets = service.list_presets()
    return ResearchPresetListResponse(
        total=len(presets),
        presets=[_preset_response(item) for item in presets],
    )


@router.post(
    "/presets",
    response_model=ResearchPresetResponse,
    summary="Save one research pipeline preset",
)
def save_research_preset(
    request: ResearchPresetRequest,
    service: ResearchPipelineServiceDependency,
) -> ResearchPresetResponse:
    preset = ResearchPreset(
        preset_id=request.preset_id,
        name=request.name,
        description=request.description,
        config=request.config.model_dump(mode="json"),
        created_at=datetime.now(UTC).replace(microsecond=0),
    )
    service.save_preset(preset)
    return _preset_response(preset)


@router.get(
    "/presets/{preset_id}",
    response_model=ResearchPresetResponse,
    summary="Read one research pipeline preset",
)
def get_research_preset(
    preset_id: str,
    service: ResearchPipelineServiceDependency,
) -> ResearchPresetResponse:
    preset = service.get_preset(preset_id)
    if preset is None:
        raise ResearchPresetNotFoundError(
            f"Unknown research preset: {preset_id}",
            details={"preset_id": preset_id},
        )
    return _preset_response(preset)


@router.get(
    "/runs/{run_id}/report",
    summary="Render one research pipeline report",
)
def get_research_report(
    run_id: str,
    service: ResearchPipelineServiceDependency,
    format: str = Query(default="markdown", pattern="^markdown$"),
) -> Response:
    report = service.render_markdown_report(run_id)
    if report is None:
        raise ResearchRunNotFoundError(
            f"Unknown research pipeline run: {run_id}",
            details={"run_id": run_id},
        )
    return Response(
        content=report,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{run_id}-research-report.md"'},
    )


@router.get(
    "/runs/{run_id}/export",
    summary="Export one research pipeline artifact",
)
def export_research_artifact(
    run_id: str,
    service: ResearchPipelineServiceDependency,
    artifact: str = Query(
        default="summary",
        pattern="^(summary|scanner|quality|portfolio|strategy)$",
    ),
    format: str = Query(default="json", pattern="^(json|csv)$"),
) -> Response:
    exported = service.export_artifact(run_id, artifact=artifact, format_=format)
    if exported is None:
        raise ResearchRunNotFoundError(
            f"Unknown research pipeline run: {run_id}",
            details={"run_id": run_id},
        )
    extension = "json" if format == "json" else "csv"
    media_type = "application/json" if format == "json" else "text/csv; charset=utf-8"
    return Response(
        content=exported,
        media_type=media_type,
        headers={
            "Content-Disposition": (f'attachment; filename="{run_id}-{artifact}.{extension}"')
        },
    )


def _preset_response(preset: ResearchPreset) -> ResearchPresetResponse:
    return ResearchPresetResponse(
        preset_id=preset.preset_id,
        name=preset.name,
        description=preset.description,
        config=preset.config,
        created_at=preset.created_at,
    )
