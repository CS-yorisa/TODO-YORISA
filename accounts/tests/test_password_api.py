import re
from datetime import timedelta

from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.auth import create_access_token, create_reauth_token
from accounts.models import Member

PASSWORD = "strong-pass-9231"
NEW_PASSWORD = "brand-new-pass-4827"

# 비밀번호 변경은 세션 갱신(update_session_auth_hash)을 검증해야 하므로
# 미들웨어를 거치는 Django Client로 테스트한다.


class ChangePasswordTest(TestCase):
    url = "/api/accounts/me/password/"

    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password=PASSWORD)
        self.web = Client()
        self.web.force_login(self.member)
        self.reauth = {"X-Reauth-Token": create_reauth_token(self.member.pk)}

    def change(self, new_password, headers=None):
        return self.web.post(
            self.url,
            data={"new_password": new_password},
            content_type="application/json",
            headers=self.reauth if headers is None else headers,
        )

    def test_비밀번호_변경_후_세션_유지(self):
        response = self.change(NEW_PASSWORD)
        self.assertEqual(response.status_code, 204)
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password(NEW_PASSWORD))
        # 세션 인증 해시가 갱신되어 로그인이 유지된다.
        self.assertEqual(self.web.get("/api/accounts/me/").status_code, 200)

    def test_JWT로_비밀번호_변경(self):
        web = Client()
        headers = {
            "Authorization": f"Bearer {create_access_token(self.member.pk)}",
            **self.reauth,
        }
        response = web.post(
            self.url,
            data={"new_password": NEW_PASSWORD},
            content_type="application/json",
            headers=headers,
        )
        self.assertEqual(response.status_code, 204)
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password(NEW_PASSWORD))

    def test_재확인_토큰_없으면_403(self):
        response = self.change(NEW_PASSWORD, headers={})
        self.assertEqual(response.status_code, 403)
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password(PASSWORD))

    @override_settings(JWT_REAUTH_TOKEN_LIFETIME=timedelta(seconds=-1))
    def test_만료된_재확인_토큰은_403(self):
        expired = {"X-Reauth-Token": create_reauth_token(self.member.pk)}
        response = self.change(NEW_PASSWORD, headers=expired)
        self.assertEqual(response.status_code, 403)

    def test_비밀번호_정책_위반은_400(self):
        response = self.change("12345678")
        self.assertEqual(response.status_code, 400)
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password(PASSWORD))

    def test_비로그인은_401(self):
        response = Client().post(
            self.url,
            data={"new_password": NEW_PASSWORD},
            content_type="application/json",
            headers=self.reauth,
        )
        self.assertEqual(response.status_code, 401)


class PasswordResetTest(TestCase):
    url = "/api/auth/password/reset/"

    def setUp(self):
        cache.clear()
        self.member = Member.objects.create_user(
            username="user1", email="user1@test.com", password=PASSWORD
        )

    def request_reset(self, username, email):
        return self.client.post(
            self.url, data={"username": username, "email": email}, content_type="application/json"
        )

    def test_일치하면_메일_발송(self):
        response = self.request_reset("user1", "USER1@test.com")
        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["user1@test.com"])
        self.assertIn("/accounts/password/reset/", mail.outbox[0].body)

    def test_일치하는_계정이_없어도_같은_응답(self):
        matched = self.request_reset("user1", "user1@test.com").json()
        unmatched = self.request_reset("user1", "other@test.com")
        self.assertEqual(unmatched.status_code, 202)
        self.assertEqual(unmatched.json(), matched)
        self.assertEqual(len(mail.outbox), 1)

    def test_탈퇴_회원에게는_발송하지_않음(self):
        Member.objects.filter(pk=self.member.pk).update(is_active=False)
        self.request_reset("user1", "user1@test.com")
        self.assertEqual(len(mail.outbox), 0)


class PasswordResetConfirmTest(TestCase):
    url = "/api/auth/password/reset/confirm/"

    def setUp(self):
        cache.clear()
        self.member = Member.objects.create_user(
            username="user1", email="user1@test.com", password=PASSWORD
        )
        self.uid = urlsafe_base64_encode(force_bytes(self.member.pk))
        self.token = default_token_generator.make_token(self.member)

    def confirm(self, uid, token, new_password=NEW_PASSWORD):
        return self.client.post(
            self.url,
            data={"uid": uid, "token": token, "new_password": new_password},
            content_type="application/json",
        )

    def test_새_비밀번호_설정(self):
        response = self.confirm(self.uid, self.token)
        self.assertEqual(response.status_code, 204)
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password(NEW_PASSWORD))

    def test_메일_링크의_uid_token으로_설정(self):
        self.client.post(
            "/api/auth/password/reset/",
            data={"username": "user1", "email": "user1@test.com"},
            content_type="application/json",
        )
        match = re.search(r"/accounts/password/reset/([^/]+)/([^/]+)/", mail.outbox[0].body)
        assert match is not None
        response = self.confirm(match.group(1), match.group(2))
        self.assertEqual(response.status_code, 204)

    def test_사용한_토큰은_재사용_불가(self):
        self.confirm(self.uid, self.token)
        response = self.confirm(self.uid, self.token, "another-new-pass-5519")
        self.assertEqual(response.status_code, 400)

    def test_잘못된_토큰은_400(self):
        response = self.confirm(self.uid, "bad-token")
        self.assertEqual(response.status_code, 400)

    def test_잘못된_uid는_400(self):
        response = self.confirm("garbage", self.token)
        self.assertEqual(response.status_code, 400)

    def test_비밀번호_정책_위반은_400(self):
        response = self.confirm(self.uid, self.token, "12345678")
        self.assertEqual(response.status_code, 400)
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password(PASSWORD))
