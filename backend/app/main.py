from fastapi import Depends, FastAPI

from app.api_errors import ApiError, api_error_handler
from app.auth import AuthenticatedPrincipal, require_authenticated_principal

app = FastAPI(title="Momentum AI")
app.add_exception_handler(ApiError, api_error_handler)


@app.get("/api/v1/auth/me")
def get_authenticated_user(
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
) -> dict[str, str]:
    return {"subject": principal.subject}
