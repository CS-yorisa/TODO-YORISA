from django.test import TestCase

from accounts.models import Member
from todos.models import Category, Todo


class TodoModelTest(TestCase):
    """Todo 모델 기본 동작 테스트"""

    def setUp(self):
        self.member = Member.objects.create_user(
            username="testuser", password="test-pass"
        )
        self.category = Category.objects.create(member=self.member, name="업무")

    def test_todo_생성_기본값(self):
        """title만으로 Todo 생성 시 기본값 검증"""
        todo = Todo.objects.create(member=self.member, title="테스트 할일")
        self.assertEqual(todo.title, "테스트 할일")
        self.assertEqual(todo.description, "")
        self.assertEqual(todo.status, Todo.Status.TODO)
        self.assertIsNone(todo.category)

    def test_todo_생성_모든_필드(self):
        """모든 필드를 지정하여 Todo 생성"""
        todo = Todo.objects.create(
            member=self.member,
            category=self.category,
            title="상세 할일",
            description="상세 설명",
            status=Todo.Status.IN_PROGRESS,
        )
        self.assertEqual(todo.title, "상세 할일")
        self.assertEqual(todo.description, "상세 설명")
        self.assertEqual(todo.status, Todo.Status.IN_PROGRESS)
        self.assertEqual(todo.category, self.category)
        self.assertEqual(todo.member, self.member)

    def test_str_method(self):
        """__str__ 이 title을 반환하는지 확인"""
        todo = Todo.objects.create(member=self.member, title="str 테스트")
        self.assertEqual(str(todo), "str 테스트")

    def test_status_choices(self):
        """Status TextChoices 값 검증"""
        self.assertEqual(Todo.Status.TODO, "todo")
        self.assertEqual(Todo.Status.IN_PROGRESS, "in_progress")
        self.assertEqual(Todo.Status.DONE, "done")

    def test_member_delete_todo_member_null(self):
        """member 삭제 시 Todo.member가 NULL로 변경되는지 확인 (SET_NULL)"""
        todo = Todo.objects.create(member=self.member, title="멤버 삭제 테스트")
        self.member.delete()
        todo.refresh_from_db()
        self.assertIsNone(todo.member)

    def test_category_delete_todo_category_null(self):
        """category 삭제 시 Todo.category가 NULL로 변경되는지 확인 (SET_NULL)"""
        todo = Todo.objects.create(
            member=self.member, category=self.category, title="카테고리 삭제 테스트"
        )
        self.category.delete()
        todo.refresh_from_db()
        self.assertIsNone(todo.category)

    def test_todo_delete(self):
        """Todo 삭제 후 DB에서 제거 확인"""
        todo = Todo.objects.create(member=self.member, title="삭제 테스트")
        todo_id = todo.id
        todo.delete()
        self.assertFalse(Todo.objects.filter(id=todo_id).exists())

    def test_category_none_creation(self):
        """category는 선택 필드(nullable)이므로 None으로 저장 가능"""
        todo = Todo.objects.create(member=self.member, title="카테고리 없음")
        self.assertIsNone(todo.category)

    def test_multiple_todos_same_member(self):
        """한 member에 여러 Todo 생성 가능"""
        Todo.objects.create(member=self.member, title="할일 1")
        Todo.objects.create(member=self.member, title="할일 2")
        Todo.objects.create(member=self.member, title="할일 3")
        self.assertEqual(Todo.objects.filter(member=self.member).count(), 3)

    def test_status_done으로_업데이트(self):
        """status를 done으로 변경 가능"""
        todo = Todo.objects.create(member=self.member, title="완료 테스트")
        todo.status = Todo.Status.DONE
        todo.save()
        todo.refresh_from_db()
        self.assertEqual(todo.status, Todo.Status.DONE)
