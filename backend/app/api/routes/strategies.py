from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.dependencies import get_strategy_template_service
from app.domain.errors import StrategyTemplateValidationError
from app.domain.strategy import (
    StrategyParameterDefinition,
    StrategyRenderContext,
    StrategyRenderResult,
    StrategyTemplate,
    StrategyValidationReport,
)
from app.schemas.strategies import (
    StrategyParameterOptionResponse,
    StrategyParameterResponse,
    StrategyRenderRequest,
    StrategyRenderResponse,
    StrategyTemplateListResponse,
    StrategyTemplateResponse,
    StrategyValidateRequest,
    StrategyValidationIssueResponse,
    StrategyValidationReportResponse,
)
from app.services.strategy_template_service import StrategyTemplateService

router = APIRouter(prefix="/strategies", tags=["strategy templates"])
StrategyServiceDependency = Annotated[
    StrategyTemplateService, Depends(get_strategy_template_service)
]


@router.get(
    "/templates",
    response_model=StrategyTemplateListResponse,
    summary="List deterministic strategy templates",
)
def list_strategy_templates(service: StrategyServiceDependency) -> StrategyTemplateListResponse:
    templates = [_template_response(template) for template in service.list_templates()]
    return StrategyTemplateListResponse(total=len(templates), templates=templates)


@router.get(
    "/templates/{template_id}",
    response_model=StrategyTemplateResponse,
    summary="Read one strategy template",
)
def get_strategy_template(
    service: StrategyServiceDependency,
    template_id: Annotated[str, Path(min_length=1, max_length=64)],
) -> StrategyTemplateResponse:
    return _template_response(service.get_template(template_id))


@router.post(
    "/render",
    response_model=StrategyRenderResponse,
    summary="Render a strategy template into Strategy JSON DSL",
)
def render_strategy(
    request: StrategyRenderRequest,
    service: StrategyServiceDependency,
) -> StrategyRenderResponse:
    if not request.template_id:
        raise StrategyTemplateValidationError("template_id is required for this render endpoint.")
    return _render_response(_render_result(request.template_id, request, service))


@router.post(
    "/templates/{template_id}/render",
    response_model=StrategyRenderResponse,
    summary="Render a path-selected template into Strategy JSON DSL",
)
def render_strategy_template(
    request: StrategyRenderRequest,
    service: StrategyServiceDependency,
    template_id: Annotated[str, Path(min_length=1, max_length=64)],
) -> StrategyRenderResponse:
    return _render_response(_render_result(template_id, request, service))


@router.post(
    "/validate",
    response_model=StrategyValidationReportResponse,
    summary="Validate a Strategy JSON DSL document",
)
def validate_strategy_document(
    request: StrategyValidateRequest,
    service: StrategyServiceDependency,
) -> StrategyValidationReportResponse:
    return _validation_response(service.validate_strategy(request.strategy_json))


def _render_result(
    template_id: str,
    request: StrategyRenderRequest,
    service: StrategyTemplateService,
) -> StrategyRenderResult:
    context = StrategyRenderContext(
        symbol=request.symbol,
        market=request.market,
        timeframe=request.timeframe,
        start=request.start,
        end=request.end,
        initial_cash=request.initial_cash,
        commission=request.commission,
        slippage=request.slippage,
    )
    return service.render_template(template_id, parameters=request.parameters, context=context)


def _render_response(result: StrategyRenderResult) -> StrategyRenderResponse:
    return StrategyRenderResponse(
        dsl_version=str(result.strategy_json.get("dsl_version", "")),
        template=_template_response(result.template),
        parameters=result.parameters,
        required_indicators=list(result.required_indicators),
        validation=_validation_response(result.validation),
        strategy_json=result.strategy_json,
    )


def _template_response(template: StrategyTemplate) -> StrategyTemplateResponse:
    default_parameters = {parameter.key: parameter.default for parameter in template.parameters}
    return StrategyTemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        category=template.category,
        summary=template.summary,
        parameters=[_parameter_response(parameter) for parameter in template.parameters],
        tags=list(template.tags),
        indicator_kinds=list(template.indicator_kinds),
        risk_notes=list(template.risk_notes),
        default_parameters=default_parameters,
        parameter_count=len(template.parameters),
        research_notes=" ".join(template.risk_notes) or template.summary,
    )


def _parameter_response(parameter: StrategyParameterDefinition) -> StrategyParameterResponse:
    return StrategyParameterResponse(
        key=parameter.key,
        label=parameter.label,
        kind=parameter.kind,
        default=parameter.default,
        description=parameter.description,
        minimum=parameter.minimum,
        maximum=parameter.maximum,
        step=parameter.step,
        unit=parameter.unit,
        options=[
            StrategyParameterOptionResponse(value=option.value, label=option.label)
            for option in parameter.options
        ],
    )


def _validation_response(report: StrategyValidationReport) -> StrategyValidationReportResponse:
    issues = [
        StrategyValidationIssueResponse(
            code=issue.code,
            severity=issue.severity,
            message=issue.message,
            path=issue.path,
            context=issue.context,
        )
        for issue in report.issues
    ]
    return StrategyValidationReportResponse(
        valid=report.is_valid,
        issue_count=len(issues),
        issues=issues,
    )
