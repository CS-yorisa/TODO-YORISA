# todos 테스트

## 파일 구조

- `test_todo_model.py` — Todo 모델 단위 테스트

## 테스트 실행

```sh
uv run python manage.py test todos.tests
```

---

## 테스트 작성 원칙

### 1. 실제 DB를 사용한다

`django.test.TestCase`를 상속한다. DB를 모킹하지 않고 실제 쿼리를 실행하여 ORM 동작(CASCADE, SET_NULL, unique_together 등)을 검증한다. 각 테스트는 트랜잭션으로 격리되어 자동 롤백된다.

### 2. setUp으로 공통 픽스처를 준비한다

테스트마다 반복되는 객체(`Member`, `Category` 등)는 `setUp`에서 `self.*`로 생성한다. 테스트 메서드 내부에서는 해당 테스트에만 필요한 객체만 추가로 생성한다.

```python
def setUp(self):
    self.member = Member.objects.create_user(username="testuser", password="test-pass")
    self.category = Category.objects.create(member=self.member, name="업무")
```

### 3. 테스트 메서드 이름은 영어로, 최대한 짧게 작성한다

`test_` 접두사 뒤에 `subject_condition` 형태로 작성한다. 명확성을 유지하면서 불필요한 단어는 제거한다.

```python
# 좋음
def test_member_null_on_delete():
def test_default_status():

# 나쁨
def test_member_삭제_시_todo_member_null():  # 한국어 금지
def test_todo_is_created_with_default_status_value():  # 과도하게 장황함
```

### 4. 상태값은 문자열 리터럴 대신 TextChoices를 사용한다

하드코딩된 문자열(`"todo"`, `"done"`) 대신 `Todo.Status.TODO`, `Todo.Status.DONE`을 사용한다. 값이 변경되어도 테스트가 자동으로 따라간다.

```python
# 좋음
self.assertEqual(todo.status, Todo.Status.IN_PROGRESS)

# 나쁨
self.assertEqual(todo.status, "in_progress")
```

### 5. DB 반영 여부는 refresh_from_db로 확인한다

`save()` 또는 외부 삭제 후 인메모리 객체를 그대로 검증하면 실제 DB 상태와 다를 수 있다. 저장 후 재조회가 필요한 경우 반드시 `refresh_from_db()`를 호출한다.

```python
todo.status = Todo.Status.DONE
todo.save()
todo.refresh_from_db()
self.assertEqual(todo.status, Todo.Status.DONE)
```

### 6. 관계 동작(CASCADE, SET_NULL)은 반드시 테스트한다

FK의 `on_delete` 옵션은 모델의 핵심 동작이므로 각각 독립적인 테스트로 검증한다. 연관 객체를 삭제한 뒤 `refresh_from_db()`로 실제 DB 상태를 확인한다.

### 7. 한 테스트에서 한 가지만 검증한다

하나의 테스트 메서드는 하나의 동작이나 제약을 검증한다. 여러 관심사를 하나의 테스트에 묶으면 실패 원인 파악이 어려워진다.

### 8. 존재 여부는 .exists()로 확인한다

삭제 후 DB에서 제거되었는지 확인할 때 `get()`으로 예외를 유도하지 않고 `filter().exists()`를 사용한다.

```python
self.assertFalse(Todo.objects.filter(id=todo_id).exists())
```

### 9. 실패·오류 케이스를 반드시 테스트한다

정상 흐름만 검증하면 제약 위반이나 잘못된 입력에 대한 동작을 보장할 수 없다. 아래 유형은 각각 독립된 테스트로 작성한다.

- **제약 위반**: `unique_together`, `null=False` 등 DB 제약을 어겼을 때 예외 발생 확인
- **잘못된 값**: 허용되지 않는 `status` 값 등 유효성 검사 실패 확인
- **존재하지 않는 객체**: 없는 ID로 조회 시 `DoesNotExist` 또는 404 확인

```python
from django.db import IntegrityError

def test_duplicate_category_name(self):
    Category.objects.create(member=self.member, name="업무")
    with self.assertRaises(IntegrityError):
        Category.objects.create(member=self.member, name="업무")

def test_title_required(self):
    with self.assertRaises(Exception):
        Todo.objects.create(member=self.member, title=None)
```
