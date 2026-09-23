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


def create_reauth_token(member_id: int) -> str:
    """비밀번호 재확인 후 발급하는 단기 토큰. 정보 수정·비밀번호 변경 API에 `X-Reauth-Token`으로 보낸다."""
    return _create_token(member_id, "reauth", settings.JWT_REAUTH_TOKEN_LIFETIME)


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    """서명·만료를 검증하고 payload를 반환한다. 실패 시 jwt.InvalidTokenError(하위 예외 포함)."""
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("token_type") != expected_type:
        raise jwt.InvalidTokenError("토큰 타입이 일치하지 않습니다.")
    return payload


class JWTAuth(HttpBearer):
    """Authorization: Bearer <access> 헤더를 검증하는 인증 클래스.

    회원 API(`profile_router`)에 세션 인증(`django_auth`)과 함께 적용되어 있다.
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
