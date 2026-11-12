from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import jwt
from dotenv import load_dotenv
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError

from app.api_errors import ApiError


class AuthConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class NeonAuthSettings:
    jwks_url: str
    issuer: str

    @classmethod
    def from_environment(cls) -> "NeonAuthSettings":
        load_dotenv(
            dotenv_path=Path(__file__).resolve().parents[1] / ".env",
            override=False,
        )

        import os

        jwks_url = os.getenv("NEON_AUTH_JWKS_URL")
        auth_base_url = os.getenv("NEON_AUTH_BASE_URL")
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
        except (PyJWTError, ValueError, KeyError) as error:
            raise InvalidAccessTokenError from error

        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise InvalidAccessTokenError
        return AuthenticatedPrincipal(subject=subject)


class InvalidAccessTokenError(Exception):
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
    except InvalidAccessTokenError:
        raise ApiError(
            status_code=401,
            code="INVALID_ACCESS_TOKEN",
            message="The access token is invalid or expired.",
        ) from None
