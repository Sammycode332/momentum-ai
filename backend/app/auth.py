from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import logging
from os import getenv
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import jwt
from dotenv import dotenv_values
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import ExpiredSignatureError, ImmatureSignatureError, PyJWKClientConnectionError, PyJWTError

from app.api_errors import ApiError

logger = logging.getLogger(__name__)


class AuthConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class NeonAuthSettings:
    jwks_url: str
    issuer: str

    @classmethod
    def from_environment(cls) -> "NeonAuthSettings":
        local = dotenv_values(Path(__file__).resolve().parents[1] / ".env", encoding="utf-8-sig")
        jwks_url = getenv("NEON_AUTH_JWKS_URL", local.get("NEON_AUTH_JWKS_URL"))
        auth_base_url = getenv("NEON_AUTH_BASE_URL", local.get("NEON_AUTH_BASE_URL"))
        if not jwks_url or not auth_base_url:
            raise AuthConfigurationError("Neon Auth verification is not configured.")

        parsed_auth_url = urlparse(auth_base_url)
        parsed_jwks_url = urlparse(jwks_url)
        if (
            parsed_auth_url.scheme != "https"
            or not parsed_auth_url.netloc
            or parsed_jwks_url.scheme != "https"
            or not parsed_jwks_url.netloc
        ):
            raise AuthConfigurationError("Neon Auth verification URLs must use HTTPS.")

        return cls(
            jwks_url=jwks_url,
            issuer=f"{parsed_auth_url.scheme}://{parsed_auth_url.netloc}",
        )


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    subject: str


class NeonAccessTokenVerifier:
    def __init__(self, settings: NeonAuthSettings, jwk_client: Any | None = None) -> None:
        self._issuer = settings.issuer
        self._jwk_client = jwk_client or PyJWKClient(settings.jwks_url)

    def verify(self, token: str) -> AuthenticatedPrincipal:
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "EdDSA":
                raise jwt.InvalidAlgorithmError("Unsupported signing algorithm.")

            signing_key = self._jwk_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["EdDSA"],
                issuer=self._issuer,
                options={"require": ["exp", "iss", "sub"], "verify_aud": False},
            )
        except ExpiredSignatureError:
            raise ExpiredAccessTokenError from None
        except ImmatureSignatureError as error:
            raise FutureAccessTokenError from error
        except PyJWKClientConnectionError:
            logger.warning("Neon Auth signing keys could not be reached")
            raise ApiError(503, "AUTH_KEYS_UNAVAILABLE", "Session verification is temporarily unavailable. Try again.") from None
        except (PyJWTError, ValueError, KeyError) as error:
            raise InvalidAccessTokenError from error

        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise InvalidAccessTokenError
        return AuthenticatedPrincipal(subject=subject)


class InvalidAccessTokenError(Exception):
    pass


class ExpiredAccessTokenError(InvalidAccessTokenError):
    pass


class FutureAccessTokenError(InvalidAccessTokenError):
    pass


bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_token_verifier() -> NeonAccessTokenVerifier:
    try:
        return NeonAccessTokenVerifier(NeonAuthSettings.from_environment())
    except AuthConfigurationError as error:
        raise ApiError(
            status_code=503,
            code="AUTH_CONFIGURATION_ERROR",
            message="Authentication is temporarily unavailable.",
        ) from error


def require_authenticated_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    verifier: NeonAccessTokenVerifier = Depends(get_token_verifier),
) -> AuthenticatedPrincipal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ApiError(
            status_code=401,
            code="UNAUTHORIZED",
            message="Authentication is required.",
        )

    try:
        return verifier.verify(credentials.credentials)
    except ExpiredAccessTokenError:
        raise ApiError(401, "ACCESS_TOKEN_EXPIRED", "Your session has expired. Sign in again to continue.") from None
    except FutureAccessTokenError:
        logger.warning("Neon JWT rejected id=%s reason=ImmatureSignatureError",
                       getattr(request.state, "diagnostic_id", "-"))
        raise ApiError(401, "ACCESS_TOKEN_NOT_YET_VALID", "Session verification could not complete. Try again.") from None
    except InvalidAccessTokenError as error:
        logger.warning(
            "Neon JWT rejected id=%s reason=%s",
            getattr(request.state, "diagnostic_id", "-"),
            type(error.__cause__).__name__ if error.__cause__ else "InvalidSubject",
        )
        raise ApiError(
            status_code=401,
            code="INVALID_ACCESS_TOKEN",
            message="The access token is invalid or expired.",
        ) from None
