from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase

from accounts.auth import create_access_token
from accounts.models import Member

# 요청 횟수 제한은 settings.NINJA_DEFAULT_THROTTLE_RATES를 따른다.
# login 10/m(IP당), verify_password 5/m(회원당), password_reset 5/h(IP당)
LOGIN_LIMIT = 10
VERIFY_PASSWORD_LIMIT = 5
PASSWORD_RESET_LIMIT = 5


def post_json(client, url, data, **kwargs):
    return client.post(url, data=data, content_type="application/json", **kwargs)


class LoginThrottleTest(TestCase):
    url = "/api/auth/login/"

    def setUp(self):
        cache.clear()
        Member.objects.create_user(username="user1", password="strong-pass-9231")
        self.client = Client()

    def exhaust(self):
        for _ in range(LOGIN_LIMIT):
            response = post_json(self.client, self.url, {"username": "user1", "password": "wrong"})
            self.assertEqual(response.status_code, 401)

    def test_제한_초과시_429(self):
        self.exhaust()
        response = post_json(self.client, self.url, {"username": "user1", "password": "wrong"})
        self.assertEqual(response.status_code, 429)

    def test_제한_초과시_올바른_비밀번호도_429(self):
        self.exhaust()
        response = post_json(
            self.client, self.url, {"username": "user1", "password": "strong-pass-9231"}
        )
        self.assertEqual(response.status_code, 429)

    def test_X_Forwarded_For_조작으로_우회_불가(self):
        # NINJA_NUM_PROXIES=0이므로 X-Forwarded-For를 무시하고 REMOTE_ADDR로 식별한다.
        self.exhaust()
        response = post_json(
            self.client,
            self.url,
            {"username": "user1", "password": "wrong"},
            headers={"X-Forwarded-For": "10.0.0.99"},
        )
        self.assertEqual(response.status_code, 429)

    def test_다른_IP는_영향_없음(self):
        self.exhaust()
        response = post_json(
            self.client,
            self.url,
            {"username": "user1", "password": "strong-pass-9231"},
            REMOTE_ADDR="10.0.0.2",
        )
        self.assertEqual(response.status_code, 200)

    def test_로그인_제한은_재설정_요청과_별도(self):
        self.exhaust()
        response = post_json(
            self.client, "/api/auth/password/reset/", {"username": "user1", "email": "x@test.com"}
        )
        self.assertEqual(response.status_code, 202)


class VerifyPasswordThrottleTest(TestCase):
    url = "/api/accounts/me/verify-password/"

    def setUp(self):
        cache.clear()
        self.member = Member.objects.create_user(username="user1", password="strong-pass-9231")
        self.other = Member.objects.create_user(username="user2", password="strong-pass-9231")
        self.client = Client()

    def verify(self, member, password):
        token = create_access_token(member.pk)
        return post_json(
            self.client,
            self.url,
            {"password": password},
            headers={"Authorization": f"Bearer {token}"},
        )

    def test_회원당_제한_초과시_429(self):
        for _ in range(VERIFY_PASSWORD_LIMIT):
            self.assertEqual(self.verify(self.member, "wrong").status_code, 400)
        self.assertEqual(self.verify(self.member, "strong-pass-9231").status_code, 429)

    def test_다른_회원은_영향_없음(self):
        for _ in range(VERIFY_PASSWORD_LIMIT):
            self.verify(self.member, "wrong")
        self.assertEqual(self.verify(self.other, "strong-pass-9231").status_code, 200)


class PasswordResetThrottleTest(TestCase):
    url = "/api/auth/password/reset/"

    def setUp(self):
        cache.clear()
        Member.objects.create_user(
            username="user1", email="user1@test.com", password="strong-pass-9231"
        )
        Member.objects.create_user(
            username="user2", email="user2@test.com", password="strong-pass-9231"
        )
        self.client = Client()

    def request_reset(self, username, email):
        return post_json(self.client, self.url, {"username": username, "email": email})

    def test_IP당_제한_초과시_429(self):
        for _ in range(PASSWORD_RESET_LIMIT):
            self.assertEqual(self.request_reset("nobody", "x@test.com").status_code, 202)
        self.assertEqual(self.request_reset("nobody", "x@test.com").status_code, 429)

    def test_같은_계정은_쿨다운_동안_메일_한_번만(self):
        first = self.request_reset("user1", "user1@test.com")
        second = self.request_reset("user1", "user1@test.com")
        # 응답은 같게 유지해 쿨다운 여부(=계정 존재 여부)가 드러나지 않게 한다.
        self.assertEqual(first.status_code, 202)
        self.assertEqual(second.json(), first.json())
        self.assertEqual(len(mail.outbox), 1)

    def test_쿨다운은_계정별(self):
        self.request_reset("user1", "user1@test.com")
        self.request_reset("user2", "user2@test.com")
        self.assertEqual(len(mail.outbox), 2)
