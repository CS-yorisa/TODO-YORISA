from django.test import TestCase
from ninja.testing import TestClient

from accounts.models import Member
from todos.models import Category, Todo
from todos.views import router

client = TestClient(router)


class TodoListTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.other = Member.objects.create_user(username="user2", password="pass")
        self.todo = Todo.objects.create(member=self.member, title="할일")

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


class TodoCreateTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.category = Category.objects.create(member=self.member, name="업무")

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
            json={"title": "할일", "category": self.category.id},
            user=self.member,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["category_id"], self.category.id)

    def test_create_other_member_category(self):
        other = Member.objects.create_user(username="user2", password="pass")
        other_category = Category.objects.create(member=other, name="타인 카테고리")
        response = client.post(
            "/",
            json={"title": "할일", "category": other_category.id},
            user=self.member,
        )
        self.assertEqual(response.status_code, 404)


class TodoDetailTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.todo = Todo.objects.create(member=self.member, title="할일")

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
            json={"title": "수정됨", "category": other_category.id},
            user=self.member,
        )
        self.assertEqual(response.status_code, 404)


class TodoPatchTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.todo = Todo.objects.create(member=self.member, title="할일")

    def test_patch_title(self):
        response = client.patch(
            f"/{self.todo.id}/",
            json={"title": "부분수정"},
            user=self.member,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "부분수정")

    def test_patch_unset_fields_unchanged(self):
        response = client.patch(
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
        response = client.patch(
            f"/{self.todo.id}/",
            json={"category": other_category.id},
            user=self.member,
        )
        self.assertEqual(response.status_code, 404)


class TodoDeleteTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.todo = Todo.objects.create(member=self.member, title="할일")

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
