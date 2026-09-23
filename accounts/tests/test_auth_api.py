from datetime import UTC, datetime, timedelta

import jwt
from django.conf import settings
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from ninja.testing import TestClient

from accounts.api import router
from accounts.auth import (
    JWTAuth,
    create_access_token,
    create_reauth_token,
    create_refresh_token,
    decode_token,
)
from accounts.models import Member, UsedRefreshToken

client = TestClient(router)


class SignupTest(TestCase):
    def test_signup(self):
        response = client.post(
            "/signup/",
            json={
                "username": "newuser",
                "email": "newuser@test.com",
                "nickname": "요리사",
                "password": "strong-pass-9231",
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["username"], "newuser")
        self.assertEqual(data["email"], "newuser@test.com")
        self.assertEqual(data["nickname"], "요리사")
        self.assertNotIn("password", data)

    def test_password_hashed(self):
        client.post(
            "/signup/",
            json={
                "username": "newuser",
                "email": "newuser@test.com",
                "nickname": "요리사",
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
            json={"username": "dup", "email": "new@test.com", "nickname": "요리사", "password": "another-pass-111"},
        )
        self.assertEqual(response.status_code, 409)

    def test_duplicate_email(self):
        Member.objects.create_user(
            username="origin", email="dup@test.com", password="strong-pass-9231"
        )
        response = client.post(
            "/signup/",
            json={"username": "newuser", "email": "dup@test.com", "nickname": "요리사", "password": "another-pass-111"},
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
            json={"username": "newuser", "email": "dup@test.com", "nickname": "요리사", "password": "another-pass-111"},
        )
        self.assertEqual(response.status_code, 201)

    def test_invalid_email_format(self):
        response = client.post(
            "/signup/",
            json={"username": "newuser", "email": "not-an-email", "nickname": "요리사", "password": "strong-pass-9231"},
        )
        self.assertEqual(response.status_code, 400)

    def test_weak_password_rejected(self):
        response = client.post(
            "/signup/",
            json={"username": "newuser", "email": "newuser@test.com", "nickname": "요리사", "password": "12345678"},
        )
        self.assertEqual(response.status_code, 400)

    def test_missing_fields(self):
        response = client.post("/signup/", json={"username": "newuser"})
        self.assertEqual(response.status_code, 422)

    def test_missing_nickname(self):
        response = client.post(
            "/signup/",
            json={"username": "newuser", "email": "newuser@test.com", "password": "strong-pass-9231"},
        )
        self.assertEqual(response.status_code, 422)

    def test_blank_nickname_rejected(self):
        response = client.post(
            "/signup/",
            json={
                "username": "newuser",
                "email": "newuser@test.com",
                "nickname": "   ",
                "password": "strong-pass-9231",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_missing_email(self):
        response = client.post(
            "/signup/", json={"username": "newuser", "password": "strong-pass-9231"}
        )
        self.assertEqual(response.status_code, 422)


class LoginTest(TestCase):
    def setUp(self):
        cache.clear()
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

    def test_withdrawn_member_rejected(self):
        refresh_token = create_refresh_token(self.member.pk)
        Member.objects.filter(pk=self.member.pk).update(
            is_active=False, withdrawn_at=timezone.now()
        )
        response = client.post("/refresh/", json={"refresh": refresh_token})
        self.assertEqual(response.status_code, 401)

    def test_reauth_token_rejected(self):
        reauth_token = create_reauth_token(self.member.pk)
        response = client.post("/refresh/", json={"refresh": reauth_token})
        self.assertEqual(response.status_code, 401)

    def test_missing_refresh_field(self):
        response = client.post("/refresh/", json={})
        self.assertEqual(response.status_code, 422)


class RefreshRotationTest(TestCase):
    """refresh 토큰을 쓸 때마다 새 refresh 토큰을 발급하고, 쓴 토큰은 다시 쓸 수 없다."""

    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="strong-pass-9231")

    def refresh(self, token):
        return client.post("/refresh/", json={"refresh": token})

    def test_new_refresh_token_issued(self):
        old_refresh = create_refresh_token(self.member.pk)
        response = self.refresh(old_refresh)
        self.assertEqual(response.status_code, 200)
        new_refresh = response.json()["refresh"]
        self.assertNotEqual(new_refresh, old_refresh)
        payload = decode_token(new_refresh, expected_type="refresh")
        self.assertEqual(payload["user_id"], self.member.pk)

    def test_used_refresh_token_rejected(self):
        old_refresh = create_refresh_token(self.member.pk)
        self.assertEqual(self.refresh(old_refresh).status_code, 200)
        self.assertEqual(self.refresh(old_refresh).status_code, 401)

    def test_new_refresh_token_usable(self):
        first = self.refresh(create_refresh_token(self.member.pk)).json()["refresh"]
        second = self.refresh(first)
        self.assertEqual(second.status_code, 200)

    def test_used_token_recorded_with_expiry(self):
        refresh_token = create_refresh_token(self.member.pk)
        payload = decode_token(refresh_token, expected_type="refresh")
        self.refresh(refresh_token)
        used = UsedRefreshToken.objects.get(jti=payload["jti"])
        self.assertEqual(int(used.expires_at.timestamp()), payload["exp"])

    def test_login_then_refresh_with_login_token(self):
        tokens = client.post(
            "/login/", json={"username": "user1", "password": "strong-pass-9231"}
        ).json()
        response = self.refresh(tokens["refresh"])
        self.assertEqual(response.status_code, 200)


class TokenInvalidatedOnPasswordChangeTest(TestCase):
    """비밀번호가 바뀌면 그 전에 발급한 access·refresh·재확인 토큰을 모두 거절한다."""

    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="strong-pass-9231")

    def change_password(self):
        self.member.set_password("brand-new-pass-4827")
        self.member.save(update_fields=["password"])

    def test_refresh_token_rejected_after_password_change(self):
        refresh_token = create_refresh_token(self.member.pk)
        self.change_password()
        response = client.post("/refresh/", json={"refresh": refresh_token})
        self.assertEqual(response.status_code, 401)

    def test_access_token_rejected_after_password_change(self):
        access_token = create_access_token(self.member.pk)
        self.change_password()
        request = type("Request", (), {})()
        self.assertIsNone(JWTAuth().authenticate(request, access_token))

    def test_token_issued_after_password_change_accepted(self):
        self.change_password()
        refresh_token = create_refresh_token(self.member.pk)
        response = client.post("/refresh/", json={"refresh": refresh_token})
        self.assertEqual(response.status_code, 200)

    def test_token_without_auth_hash_rejected(self):
        # auth_hash 검사 도입 전에 발급된 형태의 토큰
        now = datetime.now(UTC)
        legacy = jwt.encode(
            {
                "user_id": self.member.pk,
                "token_type": "refresh",
                "jti": "legacy",
                "iat": now,
                "exp": now + timedelta(days=1),
            },
            settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        response = client.post("/refresh/", json={"refresh": legacy})
        self.assertEqual(response.status_code, 401)
