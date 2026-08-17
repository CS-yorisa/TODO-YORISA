from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q


class Member(AbstractUser):
    email = models.EmailField("이메일", null=True, blank=True)
    withdrawn_at = models.DateTimeField("탈퇴일시", null=True, blank=True)

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
