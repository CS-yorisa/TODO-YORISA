from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q


class Member(AbstractUser):
    email = models.EmailField("이메일", null=True, blank=True)
    nickname = models.CharField("닉네임", max_length=30)
    withdrawn_at = models.DateTimeField("탈퇴일시", null=True, blank=True)

    # createsuperuser 실행 시 닉네임도 입력받도록 한다.
    REQUIRED_FIELDS = ["email", "nickname"]

    class Meta(AbstractUser.Meta):
        constraints = [
            # 탈퇴하지 않은 회원끼리만 email 중복을 막는다.
            # 탈퇴 회원은 email을 그대로 보존하며, 동일 email로 재가입도 가능하다.
            models.UniqueConstraint(
                fields=["email"],
                condition=Q(withdrawn_at__isnull=True),
                name="unique_active_member_email",
            ),
        ]

    def save(self, *args, **kwargs):
        # 빈 문자열을 NULL로 정규화해 email 미입력 회원 간 unique 충돌을 방지한다.
        self.email = self.email or None
        super().save(*args, **kwargs)


class Terms(models.Model):
    """회원가입 시 보여주는 약관.

    약관 내용이 바뀌면 기존 행을 수정하지 않고 새 버전을 추가한다.
    종류(kind)별로 시행일시가 지난 버전 중 가장 최근 것이 현재 약관이다.
    """

    class Kind(models.TextChoices):
        SERVICE = "service", "서비스 이용약관"
        PRIVACY = "privacy", "개인정보 수집·이용 동의"
        MARKETING = "marketing", "마케팅 정보 수신 동의"

    kind = models.CharField("종류", max_length=20, choices=Kind.choices)
    version = models.CharField("버전", max_length=20)
    title = models.CharField("제목", max_length=100)
    content = models.TextField("내용")
    is_required = models.BooleanField("필수 동의 여부", default=True)
    effective_at = models.DateTimeField("시행일시")
    created_at = models.DateTimeField("등록일시", auto_now_add=True)

    class Meta:
        verbose_name = "약관"
        verbose_name_plural = "약관"
        ordering = ["kind", "-effective_at"]
        constraints = [
            models.UniqueConstraint(fields=["kind", "version"], name="unique_terms_kind_version"),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} v{self.version}"


class UsedRefreshToken(models.Model):
    """재발급에 이미 사용한 refresh 토큰의 ID(jti).

    `/api/auth/refresh/`는 refresh 토큰을 쓸 때마다 새 refresh 토큰을 발급(rotation)하고,
    쓴 토큰의 jti를 여기 기록해 같은 토큰을 다시 쓰지 못하게 한다.
    만료된 기록은 `accounts.tasks.delete_expired_used_refresh_tokens`가 주기적으로 지운다.
    """

    jti = models.CharField("토큰 ID", max_length=32, unique=True)
    expires_at = models.DateTimeField("토큰 만료일시", db_index=True)
    used_at = models.DateTimeField("사용일시", auto_now_add=True)

    class Meta:
        verbose_name = "사용한 refresh 토큰"
        verbose_name_plural = "사용한 refresh 토큰"
