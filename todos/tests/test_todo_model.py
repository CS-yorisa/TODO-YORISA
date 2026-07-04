from django.db import IntegrityError
from django.test import TestCase

from accounts.models import Member
from todos.models import Category, Todo


class TodoModelTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(
            username="testuser", password="test-pass"
        )
        self.category = Category.objects.create(member=self.member, name="업무")

    def test_default_status(self):
        todo = Todo.objects.create(member=self.member, title="할일")
        self.assertEqual(todo.status, Todo.Status.TODO)

    def test_default_description(self):
        todo = Todo.objects.create(member=self.member, title="할일")
        self.assertEqual(todo.description, "")

    def test_default_category_none(self):
        todo = Todo.objects.create(member=self.member, title="할일")
        self.assertIsNone(todo.category)

    def test_str(self):
        todo = Todo.objects.create(member=self.member, title="할일")
        self.assertEqual(str(todo), "할일")

    def test_member_null_on_delete(self):
        todo = Todo.objects.create(member=self.member, title="할일")
        self.member.delete()
        todo.refresh_from_db()
        self.assertIsNone(todo.member)

    def test_category_null_on_delete(self):
        todo = Todo.objects.create(
            member=self.member, category=self.category, title="할일"
        )
        self.category.delete()
        todo.refresh_from_db()
        self.assertIsNone(todo.category)

    def test_status_update(self):
        todo = Todo.objects.create(member=self.member, title="할일")
        todo.status = Todo.Status.DONE
        todo.save()
        todo.refresh_from_db()
        self.assertEqual(todo.status, Todo.Status.DONE)

    def test_delete(self):
        todo = Todo.objects.create(member=self.member, title="할일")
        todo_id = todo.id
        todo.delete()
        self.assertFalse(Todo.objects.filter(id=todo_id).exists())

    def test_duplicate_category_name(self):
        with self.assertRaises(IntegrityError):
            Category.objects.create(member=self.member, name="업무")

    def test_title_null(self):
        with self.assertRaises(IntegrityError):
            Todo.objects.create(member=self.member, title=None)
