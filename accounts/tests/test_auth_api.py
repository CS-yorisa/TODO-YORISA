from datetime import UTC, datetime, timedelta

import jwt
from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from ninja.testing import TestClient

from accounts.api import router
from accounts.auth import create_access_token, create_refresh_token, decode_token
from accounts.models import Member

client = TestClient(router)


class SignupTest(TestCase):
    def test_signup(self):
        response = client.post(
            "/signup/",
            json={
                "username": "newuser",
                "email": "newuser@test.com",
                "password": "strong-pass-9231",
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["username"], "newuser")
        self.assertEqual(data["email"], "newuser@test.com")
        self.assertNotIn("password", data)

    def test_password_hashed(self):
        client.post(
            "/signup/",
            json={
                "username": "newuser",
                "email": "newuser@test.com",
                "password": "strong-pass-9231",
            },
        )
        member = Member.objects.get(username="newuser")
        self.assertTrue(member.check_password("strong-pass-9231"))

    def test_duplicate_username(self):
        Member.objects.create_user(
            username="dup", email="origin@test.com", password="strong-pass-9231"
        )
        response = client.post(
            "/signup/",
            json={"username": "dup", "email": "new@test.com", "password": "another-pass-111"},
        )
        self.assertEqual(response.status_code, 409)

    def test_duplicate_email(self):
        Member.objects.create_user(
            username="origin", email="dup@test.com", password="strong-pass-9231"
        )
        response = client.post(
            "/signup/",
            json={"username": "newuser", "email": "dup@test.com", "password": "another-pass-111"},
        )
        self.assertEqual(response.status_code, 409)

    def test_signup_with_withdrawn_member_email(self):
        Member.objects.create_user(
            username="origin", email="dup@test.com", password="strong-pass-9231"
        )
        Member.objects.filter(username="origin").update(
            is_active=False, withdrawn_at=timezone.now()
        )
        response = client.post(
            "/signup/",
            json={"username": "newuser", "email": "dup@test.com", "password": "another-pass-111"},
        )
        self.assertEqual(response.status_code, 201)

    def test_invalid_email_format(self):
        response = client.post(
            "/signup/",
            json={"username": "newuser", "email": "not-an-email", "password": "strong-pass-9231"},
        )
        self.assertEqual(response.status_code, 400)

    def test_weak_password_rejected(self):
        response = client.post(
            "/signup/",
            json={"username": "newuser", "email": "newuser@test.com", "password": "12345678"},
        )
        self.assertEqual(response.status_code, 400)

    def test_missing_fields(self):
        response = client.post("/signup/", json={"username": "newuser"})
        self.assertEqual(response.status_code, 422)

    def test_missing_email(self):
        response = client.post(
            "/signup/", json={"username": "newuser", "password": "strong-pass-9231"}
        )
        self.assertEqual(response.status_code, 422)


class LoginTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="strong-pass-9231")
        assert self.member is not None

    def test_login(self):
        self.assertIsNone(self.member.last_login)
        response = client.post(
            "/login/", json={"username": "user1", "password": "strong-pass-9231"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.member.refresh_from_db()
        self.assertIsNotNone(self.member.last_login)

    def test_wrong_password(self):
        response = client.post(
            "/login/", json={"username": "user1", "password": "wrong-password"}
        )
        self.assertEqual(response.status_code, 401)

    def test_unknown_username(self):
        response = client.post(
            "/login/", json={"username": "nouser", "password": "strong-pass-9231"}
        )
        self.assertEqual(response.status_code, 401)

    def test_missing_fields(self):
        response = client.post("/login/", json={"username": "user1"})
        self.assertEqual(response.status_code, 422)


class RefreshTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="strong-pass-9231")
        assert self.member is not None

    def test_refresh(self):
        refresh_token = create_refresh_token(self.member.pk)
        response = client.post("/refresh/", json={"refresh": refresh_token})
        self.assertEqual(response.status_code, 200)
        new_access = response.json()["access"]
        payload = decode_token(new_access, expected_type="access")
        self.assertEqual(payload["user_id"], self.member.pk)

    def test_access_token_rejected(self):
        access_token = create_access_token(self.member.pk)
        response = client.post("/refresh/", json={"refresh": access_token})
        self.assertEqual(response.status_code, 401)

    def test_expired_refresh_rejected(self):
        now = datetime.now(UTC)
        payload = {
            "user_id": self.member.pk,
            "token_type": "refresh",
            "iat": now - timedelta(days=8),
            "exp": now - timedelta(days=1),
        }
        expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        response = client.post("/refresh/", json={"refresh": expired_token})
        self.assertEqual(response.status_code, 401)

    def test_malformed_token_rejected(self):
        response = client.post("/refresh/", json={"refresh": "not-a-token"})
        self.assertEqual(response.status_code, 401)

    def test_deleted_member_rejected(self):
        refresh_token = create_refresh_token(self.member.pk)
        self.member.delete()
        response = client.post("/refresh/", json={"refresh": refresh_token})
        self.assertEqual(response.status_code, 401)
