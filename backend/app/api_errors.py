from dataclasses import dataclass
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


@dataclass
class ApiError(Exception):
    status_code: int
    code: str
    message: str
    details: dict[str, Any] | None = None


async def api_error_handler(request: Request, error: ApiError) -> JSONResponse:
    request.state.diagnostic_code = error.code
    body: dict[str, Any] = {
        "error": {
            "code": error.code,
            "message": error.message,
        }
    }
    if error.details:
        body["error"]["details"] = error.details
    return JSONResponse(status_code=error.status_code, content=body, headers={"Cache-Control": "no-store"})
