from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
from freezegun import freeze_time

from accounts.models import Member
from accounts.tasks import detect_dormant_members


@override_settings(DORMANT_MEMBER_DAYS=90)
class DetectDormantMembersTest(TestCase):
    def test_last_login_older_than_cutoff_detected(self):
        member = Member.objects.create_user(username="old", password="strong-pass-9231")
        member.last_login = timezone.now() - timedelta(days=91)
        member.save(update_fields=["last_login"])

        count = detect_dormant_members()

        self.assertEqual(count, 1)

    def test_last_login_within_cutoff_not_detected(self):
        member = Member.objects.create_user(username="recent", password="strong-pass-9231")
        member.last_login = timezone.now() - timedelta(days=10)
        member.save(update_fields=["last_login"])

        count = detect_dormant_members()

        self.assertEqual(count, 0)

    def test_never_logged_in_but_joined_long_ago_detected(self):
        with freeze_time(timezone.now() - timedelta(days=100)):
            Member.objects.create_user(username="ghost", password="strong-pass-9231")

        count = detect_dormant_members()

        self.assertEqual(count, 1)

    def test_never_logged_in_recently_joined_not_detected(self):
        Member.objects.create_user(username="newbie", password="strong-pass-9231")

        count = detect_dormant_members()

        self.assertEqual(count, 0)

    def test_withdrawn_member_excluded(self):
        member = Member.objects.create_user(username="withdrawn", password="strong-pass-9231")
        member.last_login = timezone.now() - timedelta(days=200)
        member.withdrawn_at = timezone.now()
        member.is_active = False
        member.save()

        count = detect_dormant_members()

        self.assertEqual(count, 0)

    def test_inactive_member_excluded(self):
        member = Member.objects.create_user(username="inactive", password="strong-pass-9231")
        member.last_login = timezone.now() - timedelta(days=200)
        member.is_active = False
        member.save()

        count = detect_dormant_members()

        self.assertEqual(count, 0)

    def test_task_apply_runs_synchronously(self):
        member = Member.objects.create_user(username="sync", password="strong-pass-9231")
        member.last_login = timezone.now() - timedelta(days=91)
        member.save(update_fields=["last_login"])

        result = detect_dormant_members.apply()

        self.assertTrue(result.successful())
        self.assertEqual(result.result, 1)
