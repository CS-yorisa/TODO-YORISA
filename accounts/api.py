import jwt
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
from django.utils import timezone
from ninja import Router

from accounts.auth import (
    JWTAuth,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from accounts.models import Member
from accounts.schemas import (
    AccessOut,
    ErrorOut,
    LoginIn,
    MemberOut,
    MemberUpdateIn,
    RefreshIn,
    SignupIn,
    TokenOut,
)

router = Router(tags=["auth"])
profile_router = Router(tags=["accounts"], auth=JWTAuth())


@router.post("/signup/", response={201: MemberOut, 400: ErrorOut, 409: ErrorOut})
def signup(request, payload: SignupIn):
    try:
        validate_email(payload.email)
    except ValidationError:
        return 400, {"detail": "올바른 이메일 형식이 아닙니다."}
    if Member.objects.filter(username=payload.username).exists():
        return 409, {"detail": "이미 사용 중인 사용자 이름입니다."}
    if Member.objects.filter(email=payload.email, withdrawn_at__isnull=True).exists():
        return 409, {"detail": "이미 사용 중인 이메일입니다."}
    try:
        validate_password(payload.password)
    except ValidationError as e:
        return 400, {"detail": " ".join(e.messages)}
    try:
        member = Member.objects.create_user(
            username=payload.username, email=payload.email, password=payload.password
        )
    except IntegrityError:
        # 사전 검사와 저장 사이의 동시 가입 레이스에서도 DB unique 제약 위반을 409로 응답
        return 409, {"detail": "이미 사용 중인 사용자 이름 또는 이메일입니다."}
    return 201, member


@router.post("/login/", response={200: TokenOut, 401: ErrorOut})
def login(request, payload: LoginIn):
    member = authenticate(request, username=payload.username, password=payload.password)
    if member is None:
        return 401, {"detail": "사용자 이름 또는 비밀번호가 올바르지 않습니다."}
    member.last_login = timezone.now()
    member.save(update_fields=["last_login"])
    return 200, {
        "access": create_access_token(member.pk),
        "refresh": create_refresh_token(member.pk),
    }


@router.post("/refresh/", response={200: AccessOut, 401: ErrorOut})
def refresh(request, payload: RefreshIn):
    try:
        token_payload = decode_token(payload.refresh, expected_type="refresh")
    except jwt.InvalidTokenError:
        return 401, {"detail": "유효하지 않은 토큰입니다."}
    member_id = token_payload["user_id"]
    if not Member.objects.filter(pk=member_id, is_active=True).exists():
        return 401, {"detail": "유효하지 않은 토큰입니다."}
    return 200, {"access": create_access_token(member_id)}


@profile_router.get("/me/", response=MemberOut)
def me(request):
    return request.user


@profile_router.patch("/me/", response={200: MemberOut, 409: ErrorOut})
def update_me(request, payload: MemberUpdateIn):
    data = payload.dict(exclude_unset=True)
    for attr, value in data.items():
        setattr(request.user, attr, value)
    try:
        request.user.save()
    except IntegrityError:
        return 409, {"detail": "이미 사용 중인 이메일입니다."}
    return request.user


@profile_router.delete("/me/", response={204: None})
def withdraw(request):
    member = request.user
    member.is_active = False
    member.withdrawn_at = timezone.now()
    member.save()
    return 204, None
