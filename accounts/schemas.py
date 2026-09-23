from datetime import datetime
from typing import Annotated

from ninja import Schema
from pydantic import StringConstraints

# `Member.nickname`(max_length=30, NOT NULL)과 대응한다.
# 앞뒤 공백 제거 후 길이를 검사하므로 공백만 있는 입력은 422가 된다.
Nickname = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)
]


class SignupIn(Schema):
    username: str
    email: str
    nickname: Nickname
    password: str


class LoginIn(Schema):
    username: str
    password: str


class RefreshIn(Schema):
    refresh: str


class MemberUpdateIn(Schema):
    # nickname은 NOT NULL 컬럼이므로 `| None`을 붙이지 않는다.
    # 기본값은 exclude_unset=True 때문에 사용되지 않는 자리표시자다.
    nickname: Nickname = ""
    email: str | None = None


class PasswordVerifyIn(Schema):
    password: str


class ReauthOut(Schema):
    reauth_token: str


class PasswordChangeIn(Schema):
    new_password: str


class PasswordResetIn(Schema):
    username: str
    email: str


class PasswordResetConfirmIn(Schema):
    uid: str
    token: str
    new_password: str


class MemberOut(Schema):
    id: int
    username: str
    email: str | None
    nickname: str


class TermsOut(Schema):
    """약관 응답. `kind`는 규격 밖 값이 있어도 조회가 실패하지 않도록 `str`로 둔다."""

    id: int
    kind: str
    title: str
    version: str
    content: str
    is_required: bool
    effective_at: datetime


class TokenOut(Schema):
    access: str
    refresh: str


class ErrorOut(Schema):
    detail: str


class MessageOut(Schema):
    detail: str
