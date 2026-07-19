from unittest.mock import Mock

from django.test import TestCase
from ninja.testing import TestClient

from accounts.models import Member
from accounts.views import router

client = TestClient(router)


class MemberSignupTest(TestCase):
    def test_signup(self):
        response = client.post(
            "/signup/",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "pass1234",
                "password_confirm": "pass1234",
                "first_name": "길동",
                "last_name": "홍",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["username"], "newuser")
        self.assertNotIn("password", response.json())

    def test_signup_creates_active_member(self):
        client.post(
            "/signup/",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "pass1234",
                "password_confirm": "pass1234",
            },
        )
        member = Member.objects.get(username="newuser")
        self.assertTrue(member.is_active)

    def test_signup_password_mismatch(self):
        response = client.post(
            "/signup/",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "pass1234",
                "password_confirm": "other",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_signup_duplicate_username(self):
        Member.objects.create_user(
            username="dupe", email="a@example.com", password="pass"
        )
        response = client.post(
            "/signup/",
            json={
                "username": "dupe",
                "email": "b@example.com",
                "password": "pass1234",
                "password_confirm": "pass1234",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_signup_duplicate_email(self):
        Member.objects.create_user(
            username="userA", email="dupe@example.com", password="pass"
        )
        response = client.post(
            "/signup/",
            json={
                "username": "userB",
                "email": "dupe@example.com",
                "password": "pass1234",
                "password_confirm": "pass1234",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_signup_allowed_after_withdrawal_same_username(self):
        withdrawn = Member.objects.create_user(
            username="dupe", email="a@example.com", password="pass"
        )
        withdrawn.is_active = False
        withdrawn.username = None
        withdrawn.email = None
        withdrawn.save()

        response = client.post(
            "/signup/",
            json={
                "username": "dupe",
                "email": "a@example.com",
                "password": "pass1234",
                "password_confirm": "pass1234",
            },
        )
        self.assertEqual(response.status_code, 201)


class MemberMeTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(
            username="user1", email="user1@example.com", password="pass"
        )
        assert self.member is not None

    def test_me_requires_auth(self):
        response = client.get("/me/")
        self.assertEqual(response.status_code, 401)

    def test_me(self):
        response = client.get("/me/", user=self.member)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "user1")


class MemberUpdateTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(
            username="user1", email="user1@example.com", password="pass"
        )
        assert self.member is not None

    def test_update_first_name(self):
        response = client.patch(
            "/me/", json={"first_name": "길동"}, user=self.member
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["first_name"], "길동")

    def test_update_unset_fields_unchanged(self):
        client.patch("/me/", json={"first_name": "길동"}, user=self.member)
        self.member.refresh_from_db()
        self.assertEqual(self.member.email, "user1@example.com")

    def test_update_duplicate_email(self):
        Member.objects.create_user(
            username="user2", email="user2@example.com", password="pass"
        )
        response = client.patch(
            "/me/", json={"email": "user2@example.com"}, user=self.member
        )
        self.assertEqual(response.status_code, 400)


class MemberWithdrawTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(
            username="user1", email="user1@example.com", password="pass"
        )
        assert self.member is not None

    def test_withdraw(self):
        response = client.delete("/me/", user=self.member, session=Mock())
        self.assertEqual(response.status_code, 204)
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_active)
        self.assertIsNone(self.member.username)
        self.assertIsNone(self.member.email)

    def test_withdraw_requires_auth(self):
        response = client.delete("/me/")
        self.assertEqual(response.status_code, 401)
