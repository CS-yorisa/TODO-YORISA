from django.contrib.auth.models import AbstractUser
from django.db import models


class Member(AbstractUser):
    email = models.EmailField("이메일", unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        # 빈 문자열을 NULL로 정규화해 email 미입력 회원 간 unique 충돌을 방지한다.
        self.email = self.email or None
        super().save(*args, **kwargs)
