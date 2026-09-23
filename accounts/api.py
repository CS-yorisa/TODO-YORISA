import logging

import jwt
from django.conf import settings
from django.contrib.auth import SESSION_KEY, authenticate, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import IntegrityError
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from ninja import Router
from ninja.security import django_auth
from ninja.throttling import AnonRateThrottle, UserRateThrottle

from accounts.auth import (
    JWTAuth,
    create_access_token,
    create_reauth_token,
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
    MessageOut,
    PasswordChangeIn,
    PasswordResetConfirmIn,
    PasswordResetIn,
    PasswordVerifyIn,
    ReauthOut,
    RefreshIn,
    SignupIn,
    TokenOut,
)

logger = logging.getLogger(__name__)

REAUTH_HEADER = "X-Reauth-Token"
REAUTH_REQUIRED = {"detail": "비밀번호 재확인이 필요합니다."}
PASSWORD_RESET_SENT = {"detail": "입력하신 정보와 일치하는 계정이 있으면 비밀번호 재설정 메일을 보냈습니다."}
PASSWORD_RESET_EMAIL_BODY = """{name}님, 안녕하세요.

Todo Yorisa 비밀번호 재설정 요청을 받았습니다.
아래 링크에서 새 비밀번호를 설정해 주세요. 링크는 1시간 동안, 한 번만 사용할 수 있습니다.

{reset_url}

본인이 요청하지 않았다면 이 메일을 무시하셔도 됩니다. 비밀번호는 변경되지 않습니다.
"""
INVALID_RESET_LINK = {"detail": "링크가 만료되었거나 이미 사용된 링크입니다. 다시 요청해 주세요."}



# 요청 횟수 제한. scope별 비율은 settings.NINJA_DEFAULT_THROTTLE_RATES에서 정한다.
# scope를 엔드포인트마다 따로 두어 서로의 횟수를 나눠 쓰지 않게 한다. 초과 시 429.
class LoginThrottle(AnonRateThrottle):
    scope = "login"


class PasswordResetThrottle(AnonRateThrottle):
    scope = "password_reset"


class VerifyPasswordThrottle(UserRateThrottle):
    scope = "verify_password"


router = Router(tags=["auth"])
# 웹 화면(세션 로그인)과 외부 클라이언트(JWT) 모두에서 호출할 수 있게 두 인증을 허용한다.
# 순서가 중요하다: django_auth는 CSRF 검증 실패 시 다음 인증으로 넘어가지 않고 403을 내므로,
# Authorization 헤더가 없으면 None을 반환해 넘어가는 JWTAuth를 먼저 둔다.
profile_router = Router(tags=["accounts"], auth=[JWTAuth(), django_auth])


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
            username=payload.username,
            email=payload.email,
            password=payload.password,
            nickname=payload.nickname,
        )
    except IntegrityError:
        # 사전 검사와 저장 사이의 동시 가입 레이스에서도 DB unique 제약 위반을 409로 응답
        return 409, {"detail": "이미 사용 중인 사용자 이름 또는 이메일입니다."}
    return 201, member


@router.post(
    "/login/", response={200: TokenOut, 401: ErrorOut}, throttle=[LoginThrottle()]
)
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


@router.post(
    "/password/reset/", response={202: MessageOut}, throttle=[PasswordResetThrottle()]
)
def password_reset(request, payload: PasswordResetIn):
    """아이디·이메일이 일치하는 활성 회원에게 비밀번호 재설정 링크를 메일로 보낸다.

    계정 존재 여부가 드러나지 않도록 일치 여부·발송 성공 여부와 관계없이 항상 같은 응답을 준다.
    """
    member = Member.objects.filter(
        username=payload.username.strip(),
        email__iexact=payload.email.strip(),
        is_active=True,
        withdrawn_at__isnull=True,
    ).first()
    # 같은 계정에는 쿨다운 동안 한 번만 보낸다. 응답은 동일하게 유지한다.
    if member is not None and cache.add(
        f"password_reset_sent:{member.pk}", True, settings.PASSWORD_RESET_EMAIL_COOLDOWN
    ):
        _send_password_reset_email(request, member)
    return 202, PASSWORD_RESET_SENT


@router.post("/password/reset/confirm/", response={204: None, 400: ErrorOut})
def password_reset_confirm(request, payload: PasswordResetConfirmIn):
    """메일 링크의 uid·token을 검증하고 새 비밀번호를 설정한다.

    토큰은 비밀번호 해시로 만들어지므로 비밀번호가 바뀌면 자동으로 무효화된다(1회용).
    유효 시간은 `PASSWORD_RESET_TIMEOUT`.
    """
    member = _get_member_from_uid(payload.uid)
    if member is None or not default_token_generator.check_token(member, payload.token):
        return 400, INVALID_RESET_LINK
    try:
        validate_password(payload.new_password, member)
    except ValidationError as e:
        return 400, {"detail": " ".join(e.messages)}
    member.set_password(payload.new_password)
    member.save(update_fields=["password"])
    return 204, None


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


@profile_router.post(
    "/me/verify-password/",
    response={200: ReauthOut, 400: ErrorOut},
    throttle=[VerifyPasswordThrottle()],
)
def verify_password(request, payload: PasswordVerifyIn):
    """현재 비밀번호를 재확인하고, 정보 수정·비밀번호 변경에 쓸 단기 재확인 토큰을 발급한다."""
    if not request.user.check_password(payload.password):
        return 400, {"detail": "비밀번호가 일치하지 않습니다."}
    return 200, {"reauth_token": create_reauth_token(request.user.pk)}


@profile_router.patch(
    "/me/", response={200: MemberOut, 400: ErrorOut, 403: ErrorOut, 409: ErrorOut}
)
def update_me(request, payload: MemberUpdateIn):
    if not _has_valid_reauth(request):
        return 403, REAUTH_REQUIRED
    data = payload.dict(exclude_unset=True)
    if data.get("email"):
        try:
            validate_email(data["email"])
        except ValidationError:
            return 400, {"detail": "올바른 이메일 형식이 아닙니다."}
    for attr, value in data.items():
        setattr(request.user, attr, value)
    try:
        request.user.save()
    except IntegrityError:
        return 409, {"detail": "이미 사용 중인 이메일입니다."}
    return request.user


@profile_router.post("/me/password/", response={204: None, 400: ErrorOut, 403: ErrorOut})
def change_password(request, payload: PasswordChangeIn):
    if not _has_valid_reauth(request):
        return 403, REAUTH_REQUIRED
    member = request.user
    try:
        validate_password(payload.new_password, member)
    except ValidationError as e:
        return 400, {"detail": " ".join(e.messages)}
    member.set_password(payload.new_password)
    member.save(update_fields=["password"])
    # 세션 로그인으로 호출했다면 비밀번호 해시 변경으로 세션이 끊기지 않게 갱신한다.
    # JWT로 호출한 경우엔 로그인 세션이 없으므로 건너뛴다.
    if _is_session_login(request):
        update_session_auth_hash(request, member)
    return 204, None


@profile_router.delete("/me/", response={204: None, 403: ErrorOut})
def withdraw(request):
    # 되돌릴 수 없는 작업이므로 정보 수정·비밀번호 변경과 같이 비밀번호 재확인을 요구한다.
    if not _has_valid_reauth(request):
        return 403, REAUTH_REQUIRED
    member = request.user
    member.is_active = False
    member.withdrawn_at = timezone.now()
    member.save()
    # 세션으로 호출된 경우 로그인 상태를 끊는다.
    if _is_session_login(request):
        logout(request)
    return 204, None


def _is_session_login(request) -> bool:
    """세션 로그인으로 들어온 요청인지 확인한다 (JWT 요청은 로그인 세션이 없다)."""
    session = getattr(request, "session", None)
    return session is not None and bool(session.get(SESSION_KEY))


def _has_valid_reauth(request) -> bool:
    """`X-Reauth-Token` 헤더의 재확인 토큰이 유효하고 요청한 회원 본인의 것인지 확인한다."""
    token = request.headers.get(REAUTH_HEADER)
    if not token:
        return False
    try:
        token_payload = decode_token(token, expected_type="reauth")
    except jwt.InvalidTokenError:
        return False
    return token_payload["user_id"] == request.user.pk


def _get_member_from_uid(uidb64: str) -> Member | None:
    try:
        pk = urlsafe_base64_decode(uidb64).decode()
        return Member.objects.get(pk=pk, is_active=True)
    except (ValueError, TypeError, OverflowError, ValidationError, Member.DoesNotExist):
        return None


def _send_password_reset_email(request, member: Member) -> None:
    uidb64 = urlsafe_base64_encode(force_bytes(member.pk))
    token = default_token_generator.make_token(member)
    # 메일 링크는 새 비밀번호 입력 화면으로 연결되고, 화면이 uid·token을 confirm API로 보낸다.
    reset_url = request.build_absolute_uri(
        settings.PASSWORD_RESET_URL.format(uid=uidb64, token=token)
    )
    message = PASSWORD_RESET_EMAIL_BODY.format(
        name=member.nickname or member.username, reset_url=reset_url
    )
    try:
        send_mail("[Todo Yorisa] 비밀번호 재설정 안내", message, None, [member.email])
    except Exception:
        # 발송 실패를 응답에 드러내면 계정 존재 여부가 유추되므로 로그만 남긴다.
        logger.exception("비밀번호 재설정 메일 발송 실패: member_id=%s", member.pk)
