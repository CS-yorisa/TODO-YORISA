import hmac
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from django.conf import settings
from django.http import HttpRequest
from ninja.security import HttpBearer

from accounts.models import Member


def _auth_hash(member: Member) -> str:
    """비밀번호 해시에서 파생한 값. 비밀번호가 바뀌면 달라진다.

    세션 로그인이 비밀번호 변경 시 세션을 끊을 때 쓰는 값(`get_session_auth_hash`)과 같다.
    SECRET_KEY로 서명한 HMAC이라 이 값으로 비밀번호를 알아낼 수는 없다.
    """
    return member.get_session_auth_hash()


def _create_token(member_id: int, token_type: str, lifetime: timedelta) -> str:
    # 비밀번호 해시를 토큰에 반영하기 위해 회원을 조회한다.
    member = Member.objects.get(pk=member_id)
    now = datetime.now(UTC)
    payload = {
        "user_id": member_id,
        "token_type": token_type,
        # 비밀번호가 바뀌면 이전에 발급한 토큰을 모두 무효로 만들기 위한 값
        "auth_hash": _auth_hash(member),
        # 토큰마다 고유한 ID. refresh 토큰 재사용 여부를 기록할 때 쓴다.
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + lifetime,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(member_id: int) -> str:
    return _create_token(member_id, "access", settings.JWT_ACCESS_TOKEN_LIFETIME)


def create_refresh_token(member_id: int) -> str:
    return _create_token(member_id, "refresh", settings.JWT_REFRESH_TOKEN_LIFETIME)


def create_reauth_token(member_id: int) -> str:
    """비밀번호 재확인 후 발급하는 단기 토큰. 정보 수정·비밀번호 변경·탈퇴 API에 `X-Reauth-Token`으로 보낸다."""
    return _create_token(member_id, "reauth", settings.JWT_REAUTH_TOKEN_LIFETIME)


def token_matches_member(payload: dict[str, Any], member: Member) -> bool:
    """토큰이 발급된 뒤 비밀번호가 바뀌지 않았는지 확인한다.

    `auth_hash`가 없는 토큰(이 검사 도입 전에 발급된 토큰)도 무효로 본다.
    """
    return hmac.compare_digest(str(payload.get("auth_hash", "")), _auth_hash(member))


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
        if member is None or not token_matches_member(payload, member):
            return None
        request.user = member
        return member
