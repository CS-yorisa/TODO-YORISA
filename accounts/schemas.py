from ninja import Schema


class SignupIn(Schema):
    username: str
    email: str
    password: str


class LoginIn(Schema):
    username: str
    password: str


class RefreshIn(Schema):
    refresh: str


class MemberUpdateIn(Schema):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None


class MemberOut(Schema):
    id: int
    username: str
    email: str | None
    first_name: str
    last_name: str


class TokenOut(Schema):
    access: str
    refresh: str


class AccessOut(Schema):
    access: str


class ErrorOut(Schema):
    detail: str
