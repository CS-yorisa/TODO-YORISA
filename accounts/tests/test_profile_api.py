from django.test import TestCase
from ninja.testing import TestClient

from accounts.api import profile_router
from accounts.auth import create_access_token
from accounts.models import Member

client = TestClient(profile_router)


class MemberMeTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(
            username="user1", email="user1@test.com", password="strong-pass-9231"
        )
        assert self.member is not None
        self.token = create_access_token(self.member.pk)

    def test_me(self):
        response = client.get("/me/", headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "user1")

    def test_me_requires_auth(self):
        response = client.get("/me/")
        self.assertEqual(response.status_code, 401)


class MemberUpdateTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(
            username="user1", email="user1@test.com", password="strong-pass-9231"
        )
        assert self.member is not None
        self.token = create_access_token(self.member.pk)

    def test_update_first_name(self):
        response = client.patch(
            "/me/",
            json={"first_name": "길동"},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["first_name"], "길동")

    def test_update_unset_fields_unchanged(self):
        client.patch(
            "/me/",
            json={"first_name": "길동"},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.member.refresh_from_db()
        self.assertEqual(self.member.email, "user1@test.com")

    def test_update_duplicate_email(self):
        Member.objects.create_user(
            username="user2", email="user2@test.com", password="strong-pass-9231"
        )
        response = client.patch(
            "/me/",
            json={"email": "user2@test.com"},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(response.status_code, 409)


class MemberWithdrawTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(
            username="user1", email="user1@test.com", password="strong-pass-9231"
        )
        assert self.member is not None
        self.token = create_access_token(self.member.pk)

    def test_withdraw(self):
        response = client.delete("/me/", headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 204)
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_active)
        self.assertEqual(self.member.email, "user1@test.com")
        self.assertIsNotNone(self.member.withdrawn_at)

    def test_withdraw_requires_auth(self):
        response = client.delete("/me/")
        self.assertEqual(response.status_code, 401)

    def test_token_rejected_after_withdraw(self):
        client.delete("/me/", headers={"Authorization": f"Bearer {self.token}"})
        response = client.get("/me/", headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 401)

    def test_email_reusable_after_withdraw(self):
        client.delete("/me/", headers={"Authorization": f"Bearer {self.token}"})
        member2 = Member.objects.create_user(
            username="user2", email="user1@test.com", password="strong-pass-9231"
        )
        self.assertIsNotNone(member2)
        self.assertEqual(member2.email, "user1@test.com")
