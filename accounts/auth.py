from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from django.conf import settings
from django.http import HttpRequest
from ninja.security import HttpBearer

from accounts.models import Member


def _create_token(member_id: int, token_type: str, lifetime: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {
        "user_id": member_id,
        "token_type": token_type,
        "iat": now,
        "exp": now + lifetime,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(member_id: int) -> str:
    return _create_token(member_id, "access", settings.JWT_ACCESS_TOKEN_LIFETIME)


def create_refresh_token(member_id: int) -> str:
    return _create_token(member_id, "refresh", settings.JWT_REFRESH_TOKEN_LIFETIME)


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    """서명·만료를 검증하고 payload를 반환한다. 실패 시 jwt.InvalidTokenError(하위 예외 포함)."""
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("token_type") != expected_type:
        raise jwt.InvalidTokenError("토큰 타입이 일치하지 않습니다.")
    return payload


class JWTAuth(HttpBearer):
    """Authorization: Bearer <access> 헤더를 검증하는 인증 클래스.

    현재는 어떤 라우터에도 적용하지 않으며, 추후 todos API 등에 auth=JWTAuth()로 붙여 재사용한다.
    """

    def authenticate(self, request: HttpRequest, token: str) -> Member | None:
        try:
            payload = decode_token(token, expected_type="access")
        except jwt.InvalidTokenError:
            return None
        member = Member.objects.filter(pk=payload["user_id"], is_active=True).first()
        if member is not None:
            request.user = member
        return member
