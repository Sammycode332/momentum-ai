from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api_errors import ApiError, api_error_handler
from app.auth import AuthenticatedPrincipal, require_authenticated_principal
from app.goals import router as goals_router
from app.onboarding import router as onboarding_router

app = FastAPI(title="Momentum AI")
app.add_exception_handler(ApiError, api_error_handler)
app.include_router(goals_router)
app.include_router(onboarding_router)


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
