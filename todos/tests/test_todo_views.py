from django.test import TestCase

from accounts.models import Member
from todos.models import Category, Todo


class TodoListViewTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        assert self.member is not None

    def test_requires_login(self):
        response = self.client.get("/todos/")
        self.assertEqual(response.status_code, 302)

    def test_list(self):
        Todo.objects.create(member=self.member, title="할일")
        self.client.force_login(self.member)
        response = self.client.get("/todos/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "할일")


class TodoCreateViewTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.category = Category.objects.create(member=self.member, name="업무")
        assert self.category is not None
        self.client.force_login(self.member)

    def test_create(self):
        self.client.post("/todos/create/", {"title": "새 할일"})
        self.assertTrue(Todo.objects.filter(member=self.member, title="새 할일").exists())

    def test_create_with_category(self):
        self.client.post(
            "/todos/create/", {"title": "새 할일", "category_id": self.category.id}
        )
        todo = Todo.objects.get(member=self.member, title="새 할일")
        self.assertEqual(todo.category, self.category)

    def test_create_with_due_date(self):
        self.client.post(
            "/todos/create/", {"title": "새 할일", "due_date": "2026-08-01"}
        )
        todo = Todo.objects.get(member=self.member, title="새 할일")
        self.assertEqual(str(todo.due_date), "2026-08-01")

    def test_create_blank_title_ignored(self):
        self.client.post("/todos/create/", {"title": "  "})
        self.assertFalse(Todo.objects.filter(member=self.member).exists())

    def test_create_other_member_category(self):
        other = Member.objects.create_user(username="user2", password="pass")
        other_category = Category.objects.create(member=other, name="타인 카테고리")
        response = self.client.post(
            "/todos/create/", {"title": "새 할일", "category_id": other_category.id}
        )
        self.assertEqual(response.status_code, 404)


class TodoStatusUpdateViewTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.todo = Todo.objects.create(member=self.member, title="할일")
        assert self.todo is not None
        self.client.force_login(self.member)

    def test_status_update(self):
        self.client.post(f"/todos/{self.todo.id}/status/", {"status": "done"})
        self.todo.refresh_from_db()
        self.assertEqual(self.todo.status, Todo.Status.DONE)

    def test_invalid_status_ignored(self):
        self.client.post(f"/todos/{self.todo.id}/status/", {"status": "bogus"})
        self.todo.refresh_from_db()
        self.assertEqual(self.todo.status, Todo.Status.TODO)

    def test_status_update_other_member(self):
        other = Member.objects.create_user(username="user2", password="pass")
        other_todo = Todo.objects.create(member=other, title="타인 할일")
        response = self.client.post(f"/todos/{other_todo.id}/status/", {"status": "done"})
        self.assertEqual(response.status_code, 404)


class TodoCategoryUpdateViewTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.todo = Todo.objects.create(member=self.member, title="할일")
        self.category = Category.objects.create(member=self.member, name="업무")
        assert self.todo is not None
        assert self.category is not None
        self.client.force_login(self.member)

    def test_category_update(self):
        self.client.post(
            f"/todos/{self.todo.id}/category/", {"category_id": self.category.id}
        )
        self.todo.refresh_from_db()
        self.assertEqual(self.todo.category, self.category)

    def test_category_clear(self):
        self.todo.category = self.category
        self.todo.save()
        self.client.post(f"/todos/{self.todo.id}/category/", {"category_id": ""})
        self.todo.refresh_from_db()
        self.assertIsNone(self.todo.category)

    def test_category_update_other_member_category(self):
        other = Member.objects.create_user(username="user2", password="pass")
        other_category = Category.objects.create(member=other, name="타인 카테고리")
        response = self.client.post(
            f"/todos/{self.todo.id}/category/", {"category_id": other_category.id}
        )
        self.assertEqual(response.status_code, 404)


class TodoDueDateUpdateViewTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.todo = Todo.objects.create(member=self.member, title="할일")
        assert self.todo is not None
        self.client.force_login(self.member)

    def test_due_date_update(self):
        self.client.post(f"/todos/{self.todo.id}/due-date/", {"due_date": "2026-08-01"})
        self.todo.refresh_from_db()
        self.assertEqual(str(self.todo.due_date), "2026-08-01")

    def test_due_date_clear(self):
        self.todo.due_date = "2026-08-01"
        self.todo.save()
        self.client.post(f"/todos/{self.todo.id}/due-date/", {"due_date": ""})
        self.todo.refresh_from_db()
        self.assertIsNone(self.todo.due_date)


class TodoDeleteViewTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(username="user1", password="pass")
        self.todo = Todo.objects.create(member=self.member, title="할일")
        assert self.todo is not None
        self.client.force_login(self.member)

    def test_delete(self):
        self.client.post("/todos/delete/", {"ids": str(self.todo.id)})
        self.assertFalse(Todo.objects.filter(id=self.todo.id).exists())

    def test_delete_other_member_todo_untouched(self):
        other = Member.objects.create_user(username="user2", password="pass")
        other_todo = Todo.objects.create(member=other, title="타인 할일")
        self.client.post("/todos/delete/", {"ids": str(other_todo.id)})
        self.assertTrue(Todo.objects.filter(id=other_todo.id).exists())
