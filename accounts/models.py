from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models


class Member(AbstractUser):
    """AbstractUser 기반 회원 모델.

    탈퇴 시 username/email을 NULL로 비워 unique 제약과 충돌 없이
    동일한 username/email로 재가입할 수 있게 한다(soft-delete).
    """

    username = models.CharField(
        "username",
        max_length=150,
        unique=True,
        null=True,
        help_text="150자 이하. 문자, 숫자, @/./+/-/_ 만 사용 가능합니다.",
        validators=[UnicodeUsernameValidator()],
    )
    email = models.EmailField("email address", null=True, blank=True)

    class Meta(AbstractUser.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=~models.Q(email="") & models.Q(email__isnull=False),
                name="unique_nonempty_email",
            ),
        ]
