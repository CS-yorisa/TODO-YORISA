from datetime import timedelta

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from ninja.testing import TestClient

from accounts.api import router
from accounts.models import Terms

client = TestClient(router)


def create_terms(kind, version, *, days_ago=1, is_required=True):
    return Terms.objects.create(
        kind=kind,
        version=version,
        title=f"{kind} v{version}",
        content=f"{kind} 내용 v{version}",
        is_required=is_required,
        effective_at=timezone.now() - timedelta(days=days_ago),
    )


class TermsListTest(TestCase):
    def test_로그인_없이_조회(self):
        create_terms(Terms.Kind.SERVICE, "1.0")
        response = client.get("/terms/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(data[0]["kind"], "service")
        self.assertEqual(data[0]["content"], "service 내용 v1.0")
        self.assertTrue(data[0]["is_required"])

    def test_약관이_없으면_빈_목록(self):
        response = client.get("/terms/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_종류별_최신_버전만_반환(self):
        create_terms(Terms.Kind.SERVICE, "1.0", days_ago=30)
        create_terms(Terms.Kind.SERVICE, "1.1", days_ago=1)
        data = client.get("/terms/").json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["version"], "1.1")

    def test_시행일시가_지나지_않은_버전은_제외(self):
        create_terms(Terms.Kind.SERVICE, "1.0", days_ago=1)
        create_terms(Terms.Kind.SERVICE, "2.0", days_ago=-7)  # 7일 뒤 시행 예정
        data = client.get("/terms/").json()
        self.assertEqual([t["version"] for t in data], ["1.0"])

    def test_시행_예정_약관만_있으면_빈_목록(self):
        create_terms(Terms.Kind.SERVICE, "1.0", days_ago=-1)
        self.assertEqual(client.get("/terms/").json(), [])

    def test_종류_선언_순서로_정렬(self):
        create_terms(Terms.Kind.MARKETING, "1.0", is_required=False)
        create_terms(Terms.Kind.SERVICE, "1.0")
        create_terms(Terms.Kind.PRIVACY, "1.0")
        data = client.get("/terms/").json()
        self.assertEqual([t["kind"] for t in data], ["service", "privacy", "marketing"])
        self.assertFalse(data[2]["is_required"])


class TermsModelTest(TestCase):
    def test_같은_종류_같은_버전은_중복_불가(self):
        create_terms(Terms.Kind.SERVICE, "1.0")
        with self.assertRaises(IntegrityError):
            create_terms(Terms.Kind.SERVICE, "1.0")
