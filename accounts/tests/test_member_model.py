from django.db import IntegrityError
from django.test import TestCase

from accounts.models import Member


class MemberModelTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(
            username="testuser", email="test@example.com", password="test-pass"
        )
        assert self.member is not None

    def test_duplicate_username(self):
        with self.assertRaises(IntegrityError):
            Member.objects.create_user(
                username="testuser", email="other@example.com", password="pass"
            )

    def test_duplicate_email(self):
        with self.assertRaises(IntegrityError):
            Member.objects.create_user(
                username="otheruser", email="test@example.com", password="pass"
            )

    def test_multiple_withdrawn_members_username_null(self):
        self.member.is_active = False
        self.member.username = None
        self.member.email = None
        self.member.save()

        other = Member.objects.create_user(
            username="other", email="other@example.com", password="pass"
        )
        other.is_active = False
        other.username = None
        other.email = None
        other.save()

        self.assertEqual(Member.objects.filter(username__isnull=True).count(), 2)

    def test_username_reusable_after_withdrawal(self):
        self.member.is_active = False
        self.member.username = None
        self.member.email = None
        self.member.save()

        new_member = Member.objects.create_user(
            username="testuser", email="test@example.com", password="pass"
        )
        self.assertTrue(new_member.is_active)
        self.assertEqual(new_member.username, "testuser")
