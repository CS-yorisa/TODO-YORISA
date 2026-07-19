from datetime import UTC, datetime, timedelta

import jwt
from django.conf import settings
from django.test import TestCase
from ninja import Router
from ninja.testing import TestClient

from accounts.auth import JWTAuth, create_access_token, create_refresh_token, decode_token
from accounts.models import Member

# JWTAuth 검증 전용 테스트 라우터 — 실제 API에는 마운트하지 않는다.
protected_router = Router(tags=["test"], auth=JWTAuth())


@protected_router.get("/ping/")
def ping(request):
    return {"ok": True}


protected_client = TestClient(protected_router)


class TokenUtilTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="strong-pass-9231")
        assert self.member is not None

    def test_access_token_roundtrip(self):
        token = create_access_token(self.member.pk)
        payload = decode_token(token, expected_type="access")
        self.assertEqual(payload["user_id"], self.member.pk)
        self.assertEqual(payload["token_type"], "access")

    def test_refresh_token_roundtrip(self):
        token = create_refresh_token(self.member.pk)
        payload = decode_token(token, expected_type="refresh")
        self.assertEqual(payload["token_type"], "refresh")

    def test_wrong_type_rejected(self):
        token = create_refresh_token(self.member.pk)
        with self.assertRaises(jwt.InvalidTokenError):
            decode_token(token, expected_type="access")

    def test_expired_token_rejected(self):
        now = datetime.now(UTC)
        payload = {
            "user_id": self.member.pk,
            "token_type": "access",
            "iat": now - timedelta(minutes=60),
            "exp": now - timedelta(minutes=30),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        with self.assertRaises(jwt.ExpiredSignatureError):
            decode_token(token, expected_type="access")

    def test_tampered_signature_rejected(self):
        token = create_access_token(self.member.pk)
        with self.assertRaises(jwt.InvalidTokenError):
            decode_token(token + "tampered", expected_type="access")


class JWTAuthTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="strong-pass-9231")
        assert self.member is not None

    def test_valid_token_authenticates(self):
        token = create_access_token(self.member.pk)
        response = protected_client.get("/ping/", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)

    def test_missing_header_rejected(self):
        response = protected_client.get("/ping/")
        self.assertEqual(response.status_code, 401)

    def test_invalid_token_rejected(self):
        response = protected_client.get(
            "/ping/", headers={"Authorization": "Bearer invalid-token"}
        )
        self.assertEqual(response.status_code, 401)

    def test_refresh_token_rejected(self):
        token = create_refresh_token(self.member.pk)
        response = protected_client.get("/ping/", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 401)

    def test_inactive_member_rejected(self):
        token = create_access_token(self.member.pk)
        self.member.is_active = False
        self.member.save()
        response = protected_client.get("/ping/", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 401)
