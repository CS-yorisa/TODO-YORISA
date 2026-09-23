from django.core.cache import cache
from django.test import Client, TestCase
from ninja.testing import TestClient

from accounts.api import profile_router
from accounts.auth import create_access_token, create_reauth_token
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
        self.assertIn("nickname", response.json())

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
        # 정보 수정은 비밀번호 재확인 후 발급된 재확인 토큰이 있어야 한다.
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Reauth-Token": create_reauth_token(self.member.pk),
        }

    def test_update_nickname(self):
        response = client.patch(
            "/me/",
            json={"nickname": "요리왕"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["nickname"], "요리왕")

    def test_update_nickname_null_rejected(self):
        # NOT NULL 컬럼이므로 명시적 null은 DB까지 가지 않고 422로 거절된다.
        response = client.patch(
            "/me/",
            json={"nickname": None},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 422)

    def test_update_nickname_too_long_rejected(self):
        response = client.patch(
            "/me/",
            json={"nickname": "가" * 31},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 422)

    def test_update_unset_fields_unchanged(self):
        client.patch(
            "/me/",
            json={"nickname": "요리왕"},
            headers=self.headers,
        )
        self.member.refresh_from_db()
        self.assertEqual(self.member.email, "user1@test.com")

    def test_update_invalid_email_rejected(self):
        response = client.patch(
            "/me/",
            json={"email": "not-an-email"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 400)

    def test_update_duplicate_email(self):
        Member.objects.create_user(
            username="user2", email="user2@test.com", password="strong-pass-9231"
        )
        response = client.patch(
            "/me/",
            json={"email": "user2@test.com"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 409)

    def test_update_without_reauth_token_rejected(self):
        response = client.patch(
            "/me/",
            json={"nickname": "요리왕"},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(response.status_code, 403)
        self.member.refresh_from_db()
        self.assertEqual(self.member.nickname, "")

    def test_update_with_access_token_as_reauth_rejected(self):
        # 토큰 타입이 다르면(access) 재확인 토큰으로 인정하지 않는다.
        response = client.patch(
            "/me/",
            json={"nickname": "요리왕"},
            headers={"Authorization": f"Bearer {self.token}", "X-Reauth-Token": self.token},
        )
        self.assertEqual(response.status_code, 403)

    def test_update_with_other_members_reauth_token_rejected(self):
        other = Member.objects.create_user(username="user2", password="strong-pass-9231")
        response = client.patch(
            "/me/",
            json={"nickname": "요리왕"},
            headers={
                "Authorization": f"Bearer {self.token}",
                "X-Reauth-Token": create_reauth_token(other.pk),
            },
        )
        self.assertEqual(response.status_code, 403)


class VerifyPasswordTest(TestCase):
    def setUp(self):
        cache.clear()
        self.member = Member.objects.create_user(username="user1", password="strong-pass-9231")
        self.token = create_access_token(self.member.pk)

    def test_correct_password_returns_reauth_token(self):
        response = client.post(
            "/me/verify-password/",
            json={"password": "strong-pass-9231"},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(response.status_code, 200)
        reauth_token = response.json()["reauth_token"]
        # 발급된 토큰으로 정보 수정이 가능하다.
        response = client.patch(
            "/me/",
            json={"nickname": "요리왕"},
            headers={"Authorization": f"Bearer {self.token}", "X-Reauth-Token": reauth_token},
        )
        self.assertEqual(response.status_code, 200)

    def test_wrong_password_rejected(self):
        response = client.post(
            "/me/verify-password/",
            json={"password": "wrong-pass"},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("reauth_token", response.json())

    def test_requires_auth(self):
        response = client.post("/me/verify-password/", json={"password": "strong-pass-9231"})
        self.assertEqual(response.status_code, 401)


class MemberWithdrawTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(
            username="user1", email="user1@test.com", password="strong-pass-9231"
        )
        assert self.member is not None
        self.token = create_access_token(self.member.pk)
        # 탈퇴는 비밀번호 재확인 후 발급된 재확인 토큰이 있어야 한다.
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Reauth-Token": create_reauth_token(self.member.pk),
        }

    def test_withdraw(self):
        response = client.delete("/me/", headers=self.headers)
        self.assertEqual(response.status_code, 204)
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_active)
        self.assertEqual(self.member.email, "user1@test.com")
        self.assertIsNotNone(self.member.withdrawn_at)

    def test_withdraw_without_reauth_token_rejected(self):
        response = client.delete("/me/", headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 403)
        self.member.refresh_from_db()
        self.assertTrue(self.member.is_active)
        self.assertIsNone(self.member.withdrawn_at)

    def test_withdraw_with_other_members_reauth_token_rejected(self):
        other = Member.objects.create_user(username="user2", password="strong-pass-9231")
        response = client.delete(
            "/me/",
            headers={
                "Authorization": f"Bearer {self.token}",
                "X-Reauth-Token": create_reauth_token(other.pk),
            },
        )
        self.assertEqual(response.status_code, 403)
        self.member.refresh_from_db()
        self.assertTrue(self.member.is_active)

    def test_withdraw_requires_auth(self):
        response = client.delete("/me/")
        self.assertEqual(response.status_code, 401)

    def test_token_rejected_after_withdraw(self):
        client.delete("/me/", headers=self.headers)
        response = client.get("/me/", headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 401)

    def test_email_reusable_after_withdraw(self):
        client.delete("/me/", headers=self.headers)
        member2 = Member.objects.create_user(
            username="user2", email="user1@test.com", password="strong-pass-9231"
        )
        self.assertIsNotNone(member2)
        self.assertEqual(member2.email, "user1@test.com")


class MemberSessionAuthTest(TestCase):
    """웹 화면에서 로그인한 세션으로도 회원 API를 호출할 수 있는지 검증한다.

    ninja TestClient는 미들웨어를 거치지 않으므로 세션 인증은 Django Client로 검증한다.
    """

    def setUp(self):
        self.member = Member.objects.create_user(
            username="user1",
            email="user1@test.com",
            password="strong-pass-9231",
            nickname="요리사",
        )
        self.web = Client()
        self.web.force_login(self.member)
        self.reauth = {"X-Reauth-Token": create_reauth_token(self.member.pk)}

    def test_me_with_session(self):
        response = self.web.get("/api/accounts/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["nickname"], "요리사")

    def test_update_with_session(self):
        response = self.web.patch(
            "/api/accounts/me/",
            data={"nickname": "요리왕"},
            content_type="application/json",
            headers=self.reauth,
        )
        self.assertEqual(response.status_code, 200)
        self.member.refresh_from_db()
        self.assertEqual(self.member.nickname, "요리왕")

    def test_update_with_session_requires_csrf(self):
        web = Client(enforce_csrf_checks=True)
        web.force_login(self.member)
        response = web.patch(
            "/api/accounts/me/",
            data={"nickname": "요리왕"},
            content_type="application/json",
            headers=self.reauth,
        )
        self.assertEqual(response.status_code, 403)

    def test_jwt_patch_without_csrf_allowed(self):
        # JWT 요청은 CSRF 검사 대상이 아니다(JWTAuth가 django_auth보다 먼저 처리).
        web = Client(enforce_csrf_checks=True)
        token = create_access_token(self.member.pk)
        response = web.patch(
            "/api/accounts/me/",
            data={"nickname": "요리왕"},
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}", **self.reauth},
        )
        self.assertEqual(response.status_code, 200)

    def test_withdraw_with_session_logs_out(self):
        response = self.web.delete("/api/accounts/me/", headers=self.reauth)
        self.assertEqual(response.status_code, 204)
        response = self.web.get("/api/accounts/me/")
        self.assertEqual(response.status_code, 401)


class ReauthTokenInvalidatedOnPasswordChangeTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="strong-pass-9231")

    def test_reauth_token_rejected_after_password_change(self):
        reauth_token = create_reauth_token(self.member.pk)
        self.member.set_password("brand-new-pass-4827")
        self.member.save(update_fields=["password"])
        # 비밀번호 변경 후 새로 받은 access 토큰 + 변경 전 재확인 토큰
        response = client.patch(
            "/me/",
            json={"nickname": "요리왕"},
            headers={
                "Authorization": f"Bearer {create_access_token(self.member.pk)}",
                "X-Reauth-Token": reauth_token,
            },
        )
        self.assertEqual(response.status_code, 403)
