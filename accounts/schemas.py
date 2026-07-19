from datetime import datetime

from ninja import Schema
from pydantic import EmailStr


class MemberSignupIn(Schema):
    username: str
    email: EmailStr
    password: str
    password_confirm: str
    first_name: str = ""
    last_name: str = ""


class MemberUpdateIn(Schema):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None


class MemberOut(Schema):
    id: int
    username: str
    email: str | None
    first_name: str
    last_name: str
    date_joined: datetime
