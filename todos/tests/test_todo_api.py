from datetime import date

from django.test import TestCase
from ninja.testing import TestClient

from accounts.models import Member
from todos.models import Category, Todo
from todos.api import router

client = TestClient(router)


class TodoListTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.other = Member.objects.create_user(username="user2", password="pass")
        self.todo = Todo.objects.create(member=self.member, title="할일")
        assert self.todo is not None

    def test_list(self):
        response = client.get("/", user=self.member)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_list_excludes_other_member(self):
        Todo.objects.create(member=self.other, title="타인 할일")
        response = client.get("/", user=self.member)
        self.assertEqual(len(response.json()), 1)

    def test_list_filter_by_status(self):
        Todo.objects.create(member=self.member, title="완료", status=Todo.Status.DONE)
        response = client.get("/", user=self.member, query_params={"status": "done"})
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["status"], Todo.Status.DONE)

    def test_list_invalid_status_filter(self):
        response = client.get("/", user=self.member, query_params={"status": "bogus"})
        self.assertEqual(response.status_code, 422)

    def test_list_includes_due_date(self):
        response = client.get("/", user=self.member)
        self.assertIn("due_date", response.json()[0])


class TodoCreateTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.category = Category.objects.create(member=self.member, name="업무")
        assert self.category is not None

    def test_create(self):
        response = client.post(
            "/",
            json={"title": "새 할일"},
            user=self.member,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["title"], "새 할일")

    def test_create_with_category(self):
        response = client.post(
            "/",
            json={"title": "할일", "category": self.category.pk},
            user=self.member,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["category_id"], self.category.pk)

    def test_create_other_member_category(self):
        other = Member.objects.create_user(username="user2", password="pass")
        other_category = Category.objects.create(member=other, name="타인 카테고리")
        response = client.post(
            "/",
            json={"title": "할일", "category": other_category.pk},
            user=self.member,
        )
        self.assertEqual(response.status_code, 404)

    def test_create_empty_title(self):
        response = client.post("/", json={"title": ""}, user=self.member)
        self.assertEqual(response.status_code, 422)

    def test_create_whitespace_title(self):
        response = client.post("/", json={"title": "   "}, user=self.member)
        self.assertEqual(response.status_code, 422)

    def test_create_null_title(self):
        response = client.post("/", json={"title": None}, user=self.member)
        self.assertEqual(response.status_code, 422)

    def test_create_title_too_long(self):
        response = client.post("/", json={"title": "가" * 201}, user=self.member)
        self.assertEqual(response.status_code, 422)

    def test_create_title_stripped(self):
        response = client.post("/", json={"title": "  할일  "}, user=self.member)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["title"], "할일")

    def test_create_invalid_status(self):
        response = client.post(
            "/",
            json={"title": "할일", "status": "bogus"},
            user=self.member,
        )
        self.assertEqual(response.status_code, 422)

    def test_create_valid_status(self):
        response = client.post(
            "/",
            json={"title": "할일", "status": Todo.Status.IN_PROGRESS},
            user=self.member,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], Todo.Status.IN_PROGRESS)

    def test_create_default_status(self):
        response = client.post("/", json={"title": "할일"}, user=self.member)
        self.assertEqual(response.json()["status"], Todo.Status.TODO)

    def test_create_with_due_date(self):
        response = client.post(
            "/",
            json={"title": "할일", "due_date": date(2026, 12, 25)},
            user=self.member,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Todo.objects.get(id=response.json()["id"]).due_date, date(2026, 12, 25)
        )

    def test_create_invalid_due_date(self):
        response = client.post(
            "/",
            json={"title": "할일", "due_date": "not-a-date"},
            user=self.member,
        )
        self.assertEqual(response.status_code, 422)


class TodoDetailTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.todo = Todo.objects.create(member=self.member, title="할일")
        assert self.todo is not None

    def test_detail(self):
        response = client.get(f"/{self.todo.id}/", user=self.member)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.todo.id)

    def test_detail_other_member(self):
        other = Member.objects.create_user(username="user2", password="pass")
        response = client.get(f"/{self.todo.id}/", user=other)
        self.assertEqual(response.status_code, 404)

    def test_detail_not_found(self):
        response = client.get("/99999/", user=self.member)
        self.assertEqual(response.status_code, 404)


class TodoUpdateTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.todo = Todo.objects.create(member=self.member, title="할일")
        assert self.todo is not None

    def test_update(self):
        response = client.put(
            f"/{self.todo.id}/",
            json={"title": "수정됨", "status": "done"},
            user=self.member,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "수정됨")

    def test_update_other_member(self):
        other = Member.objects.create_user(username="user2", password="pass")
        response = client.put(
            f"/{self.todo.id}/",
            json={"title": "수정됨"},
            user=other,
        )
        self.assertEqual(response.status_code, 404)

    def test_update_other_member_category(self):
        other = Member.objects.create_user(username="user2", password="pass")
        other_category = Category.objects.create(member=other, name="타인 카테고리")
        response = client.put(
            f"/{self.todo.id}/",
            json={"title": "수정됨", "category": other_category.pk},
            user=self.member,
        )
        self.assertEqual(response.status_code, 404)

    def test_update_with_due_date(self):
        response = client.put(
            f"/{self.todo.id}/",
            json={"title": "수정됨", "due_date": date(2026, 12, 25)},
            user=self.member,
        )
        self.assertEqual(response.status_code, 200)
        self.todo.refresh_from_db()
        self.assertEqual(self.todo.due_date, date(2026, 12, 25))

    def test_update_clears_due_date_when_omitted(self):
        self.todo.due_date = date(2026, 12, 25)
        self.todo.save()
        client.put(f"/{self.todo.id}/", json={"title": "수정됨"}, user=self.member)
        self.todo.refresh_from_db()
        self.assertIsNone(self.todo.due_date)

    def test_update_invalid_status(self):
        response = client.put(
            f"/{self.todo.id}/",
            json={"title": "수정됨", "status": "bogus"},
            user=self.member,
        )
        self.assertEqual(response.status_code, 422)

    def test_update_empty_title(self):
        response = client.put(
            f"/{self.todo.id}/",
            json={"title": ""},
            user=self.member,
        )
        self.assertEqual(response.status_code, 422)


class TodoPatchTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.todo = Todo.objects.create(member=self.member, title="할일")
        assert self.todo is not None

    def test_patch_title(self):
        response = client.patch(
            f"/{self.todo.id}/",
            json={"title": "부분수정"},
            user=self.member,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "부분수정")

    def test_patch_unset_fields_unchanged(self):
        client.patch(
            f"/{self.todo.id}/",
            json={"title": "부분수정"},
            user=self.member,
        )
        self.todo.refresh_from_db()
        self.assertEqual(self.todo.status, Todo.Status.TODO)

    def test_patch_other_member(self):
        other = Member.objects.create_user(username="user2", password="pass")
        response = client.patch(
            f"/{self.todo.id}/",
            json={"title": "부분수정"},
            user=other,
        )
        self.assertEqual(response.status_code, 404)

    def test_patch_other_member_category(self):
        other = Member.objects.create_user(username="user2", password="pass")
        other_category = Category.objects.create(member=other, name="타인 카테고리")
        assert other_category is not None
        response = client.patch(
            f"/{self.todo.id}/",
            json={"category": other_category.pk},
            user=self.member,
        )
        self.assertEqual(response.status_code, 404)

    def test_patch_null_title(self):
        response = client.patch(
            f"/{self.todo.id}/", json={"title": None}, user=self.member
        )
        self.assertEqual(response.status_code, 422)

    def test_patch_null_description(self):
        response = client.patch(
            f"/{self.todo.id}/", json={"description": None}, user=self.member
        )
        self.assertEqual(response.status_code, 422)

    def test_patch_null_status(self):
        response = client.patch(
            f"/{self.todo.id}/", json={"status": None}, user=self.member
        )
        self.assertEqual(response.status_code, 422)

    def test_patch_empty_title(self):
        response = client.patch(
            f"/{self.todo.id}/", json={"title": ""}, user=self.member
        )
        self.assertEqual(response.status_code, 422)

    def test_patch_title_too_long(self):
        response = client.patch(
            f"/{self.todo.id}/", json={"title": "가" * 201}, user=self.member
        )
        self.assertEqual(response.status_code, 422)

    def test_patch_invalid_status(self):
        response = client.patch(
            f"/{self.todo.id}/", json={"status": "bogus"}, user=self.member
        )
        self.assertEqual(response.status_code, 422)

    def test_patch_status(self):
        response = client.patch(
            f"/{self.todo.id}/",
            json={"status": Todo.Status.DONE},
            user=self.member,
        )
        self.assertEqual(response.status_code, 200)
        self.todo.refresh_from_db()
        self.assertEqual(self.todo.status, Todo.Status.DONE)

    def test_patch_due_date(self):
        response = client.patch(
            f"/{self.todo.id}/",
            json={"due_date": date(2026, 12, 25)},
            user=self.member,
        )
        self.assertEqual(response.status_code, 200)
        self.todo.refresh_from_db()
        self.assertEqual(self.todo.due_date, date(2026, 12, 25))

    def test_patch_null_due_date_clears(self):
        self.todo.due_date = date(2026, 12, 25)
        self.todo.save()
        client.patch(f"/{self.todo.id}/", json={"due_date": None}, user=self.member)
        self.todo.refresh_from_db()
        self.assertIsNone(self.todo.due_date)

    def test_patch_null_category_clears(self):
        category = Category.objects.create(member=self.member, name="업무")
        self.todo.category = category
        self.todo.save()
        client.patch(f"/{self.todo.id}/", json={"category": None}, user=self.member)
        self.todo.refresh_from_db()
        self.assertIsNone(self.todo.category_id)

    def test_patch_empty_body_keeps_fields(self):
        client.patch(f"/{self.todo.id}/", json={}, user=self.member)
        self.todo.refresh_from_db()
        self.assertEqual(self.todo.title, "할일")


class TodoDeleteTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.todo = Todo.objects.create(member=self.member, title="할일")
        assert self.todo is not None

    def test_delete(self):
        response = client.delete(f"/{self.todo.id}/", user=self.member)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Todo.objects.filter(id=self.todo.id).exists())

    def test_delete_other_member(self):
        other = Member.objects.create_user(username="user2", password="pass")
        response = client.delete(f"/{self.todo.id}/", user=other)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Todo.objects.filter(id=self.todo.id).exists())

    def test_delete_not_found(self):
        response = client.delete("/99999/", user=self.member)
        self.assertEqual(response.status_code, 404)
