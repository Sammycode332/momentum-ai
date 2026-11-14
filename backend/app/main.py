import logging
from pathlib import Path
from time import perf_counter
from traceback import extract_tb
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api_errors import ApiError, api_error_handler
from app.auth import AuthenticatedPrincipal, require_authenticated_principal
from app.conversation import router as conversation_router
from app.conversation_history import router as conversation_history_router
from app.goals import router as goals_router
from app.onboarding import router as onboarding_router
from app.records import router as records_router
from app.planning import router as planning_router
from app.memory import router as memory_router
from app.practice import router as practice_router
from app.reminders import router as reminders_router
from app.actions import router as actions_router
from app.discovery import router as discovery_router
from app.limits import require_ai_budget, BodyLimitMiddleware
from app.push import router as push_router
from app.account import router as account_router

logger = logging.getLogger(__name__)
app = FastAPI(title="Momentum AI")
app.add_exception_handler(ApiError, api_error_handler)
app.include_router(goals_router)
app.include_router(onboarding_router)
app.include_router(memory_router)
app.add_middleware(BodyLimitMiddleware)
app.include_router(practice_router, dependencies=[Depends(require_ai_budget)])
app.include_router(reminders_router)
app.include_router(actions_router, dependencies=[Depends(require_ai_budget)])
app.include_router(discovery_router)
app.include_router(push_router)
app.include_router(account_router)
app.include_router(planning_router, dependencies=[Depends(require_ai_budget)])
app.include_router(conversation_router, dependencies=[Depends(require_ai_budget)])
app.include_router(conversation_history_router, dependencies=[Depends(require_ai_budget)])
app.include_router(records_router)


@app.get('/health/live', include_in_schema=False)
def liveness():
    return {'status': 'ok'}


@app.middleware("http")
async def diagnose_private_api(request: Request, call_next):
    if not request.url.path.startswith("/api/v1/"):
        return await call_next(request)

    request_id = uuid4().hex
    request.state.diagnostic_id = request_id
    started = perf_counter()
    try:
        response = await call_next(request)
    except Exception as error:
        # Exception strings and source lines may contain private request or provider data.
        frames = " > ".join(
            f"{Path(frame.filename).name}:{frame.lineno}:{frame.name}"
            for frame in extract_tb(error.__traceback__)[-12:]
        )
        logger.error("API exception id=%s type=%s frames=%s", request_id, type(error).__name__, frames)
        response = await api_error_handler(
            request, ApiError(500, "INTERNAL_ERROR", "The request failed unexpectedly. Try again."),
        )

    response.headers["X-Request-ID"] = request_id
    response.headers["Cache-Control"] = "no-store"
    route = getattr(request.scope.get("route"), "path", "<unmatched>")
    if response.status_code >= 400:
        logger.warning(
            "API failure id=%s route=%s status=%d code=%s elapsed_ms=%d",
            request_id, route, response.status_code,
            getattr(request.state, "diagnostic_code", "HTTP_ERROR"),
            (perf_counter() - started) * 1000,
        )
    return response


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, _: RequestValidationError) -> JSONResponse:
    return await api_error_handler(
        request, ApiError(422, "INVALID_REQUEST", "Check the request fields and try again.")
    )


@app.get("/api/v1/auth/me")
def get_authenticated_user(
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
) -> dict[str, str]:
    return {"subject": principal.subject}
