from django.test import TestCase
from ninja.testing import TestClient

from accounts.models import Member
from todos.models import Category
from todos.api import router

client = TestClient(router)


class CategoryListTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.other = Member.objects.create_user(username="user2", password="pass")
        self.category = Category.objects.create(member=self.member, name="업무")
        assert self.category is not None

    def test_list(self):
        response = client.get("/categories/", user=self.member)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_list_excludes_other_member(self):
        Category.objects.create(member=self.other, name="타인 카테고리")
        response = client.get("/categories/", user=self.member)
        self.assertEqual(len(response.json()), 1)

    def test_list_requires_auth(self):
        response = client.get("/categories/")
        self.assertEqual(response.status_code, 401)


class CategoryCreateTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        assert self.member is not None

    def test_create(self):
        response = client.post(
            "/categories/", json={"name": "업무"}, user=self.member
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["name"], "업무")

    def test_create_duplicate_name(self):
        Category.objects.create(member=self.member, name="업무")
        response = client.post(
            "/categories/", json={"name": "업무"}, user=self.member
        )
        self.assertEqual(response.status_code, 400)

    def test_create_same_name_different_member_allowed(self):
        other = Member.objects.create_user(username="user2", password="pass")
        Category.objects.create(member=other, name="업무")
        response = client.post(
            "/categories/", json={"name": "업무"}, user=self.member
        )
        self.assertEqual(response.status_code, 201)

    def test_create_empty_name(self):
        response = client.post("/categories/", json={"name": ""}, user=self.member)
        self.assertEqual(response.status_code, 422)

    def test_create_null_name(self):
        response = client.post("/categories/", json={"name": None}, user=self.member)
        self.assertEqual(response.status_code, 422)

    def test_create_name_too_long(self):
        response = client.post(
            "/categories/", json={"name": "가" * 51}, user=self.member
        )
        self.assertEqual(response.status_code, 422)

    def test_create_name_stripped(self):
        response = client.post(
            "/categories/", json={"name": "  업무  "}, user=self.member
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["name"], "업무")


class CategoryDetailTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.category = Category.objects.create(member=self.member, name="업무")
        assert self.category is not None

    def test_detail(self):
        response = client.get(f"/categories/{self.category.id}/", user=self.member)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.category.id)

    def test_detail_other_member(self):
        other = Member.objects.create_user(username="user2", password="pass")
        response = client.get(f"/categories/{self.category.id}/", user=other)
        self.assertEqual(response.status_code, 404)

    def test_detail_not_found(self):
        response = client.get("/categories/99999/", user=self.member)
        self.assertEqual(response.status_code, 404)


class CategoryPatchTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.category = Category.objects.create(member=self.member, name="업무")
        assert self.category is not None

    def test_patch_name(self):
        response = client.patch(
            f"/categories/{self.category.id}/",
            json={"name": "개인"},
            user=self.member,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "개인")

    def test_patch_duplicate_name(self):
        Category.objects.create(member=self.member, name="개인")
        response = client.patch(
            f"/categories/{self.category.id}/",
            json={"name": "개인"},
            user=self.member,
        )
        self.assertEqual(response.status_code, 400)

    def test_patch_null_name(self):
        response = client.patch(
            f"/categories/{self.category.id}/",
            json={"name": None},
            user=self.member,
        )
        self.assertEqual(response.status_code, 422)

    def test_patch_empty_name(self):
        response = client.patch(
            f"/categories/{self.category.id}/",
            json={"name": ""},
            user=self.member,
        )
        self.assertEqual(response.status_code, 422)

    def test_patch_name_too_long(self):
        response = client.patch(
            f"/categories/{self.category.id}/",
            json={"name": "가" * 51},
            user=self.member,
        )
        self.assertEqual(response.status_code, 422)

    def test_patch_empty_body_keeps_name(self):
        client.patch(
            f"/categories/{self.category.id}/", json={}, user=self.member
        )
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "업무")

    def test_patch_other_member(self):
        other = Member.objects.create_user(username="user2", password="pass")
        response = client.patch(
            f"/categories/{self.category.id}/",
            json={"name": "개인"},
            user=other,
        )
        self.assertEqual(response.status_code, 404)


class CategoryDeleteTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.category = Category.objects.create(member=self.member, name="업무")
        assert self.category is not None

    def test_delete(self):
        response = client.delete(f"/categories/{self.category.id}/", user=self.member)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Category.objects.filter(id=self.category.id).exists())

    def test_delete_other_member(self):
        other = Member.objects.create_user(username="user2", password="pass")
        response = client.delete(f"/categories/{self.category.id}/", user=other)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Category.objects.filter(id=self.category.id).exists())
