import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from accounts.models import Member

logger = logging.getLogger(__name__)


@shared_task(name="accounts.tasks.detect_dormant_members")
def detect_dormant_members() -> int:
    """활성 회원 중 장기 미접속(휴면) 회원을 탐지해 로그로 남긴다.

    한 번도 로그인하지 않은 회원(last_login is NULL)은 가입일 기준으로 판정한다.
    """
    cutoff = timezone.now() - timedelta(days=settings.DORMANT_MEMBER_DAYS)

    dormant_qs = Member.objects.filter(
        is_active=True,
        withdrawn_at__isnull=True,
    ).filter(Q(last_login__lt=cutoff) | Q(last_login__isnull=True, date_joined__lt=cutoff))

    count = 0
    for member in dormant_qs.iterator():
        logger.info(
            "휴면 회원 탐지: id=%s username=%s last_login=%s date_joined=%s",
            member.pk,
            member.username,
            member.last_login,
            member.date_joined,
        )
        count += 1

    logger.info("휴면 회원 탐지 작업 완료: 총 %d명 (기준: %d일)", count, settings.DORMANT_MEMBER_DAYS)
    return count
