"""Protects admin-only endpoints (data sync, discovery triggers) behind a
bearer token. If ``ADMIN_API_TOKEN`` is unset, admin endpoints stay open —
suitable for local development only; production deployments must set it.
"""
from __future__ import annotations

from fastapi import Header, HTTPException, status

from .config import get_settings


def require_admin_token(authorization: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not settings.is_admin_protected:
        return

    expected = f"Bearer {settings.admin_api_token}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton d'administration invalide ou manquant.",
        )
