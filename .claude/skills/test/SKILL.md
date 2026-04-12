# Django 테스트 코드 작성 스킬

이 스킬은 현재 Django 프로젝트의 테스트 코드를 작성한다.

## 프로젝트 컨텍스트

- **프레임워크**: Django 6 + django-ninja (REST API)
- **인증**: `accounts.Member` 커스텀 유저 모델 (`AUTH_USER_MODEL = "accounts.Member"`)
- **핵심 앱**: `todos` — `Todo`, `Category` 모델 + django-ninja CRUD API
- **테스트 클라이언트**: django-ninja의 `TestClient` 사용 (`from ninja.testing import TestClient`)

## 테스트 작성 규칙

### 1. 테스트 클라이언트 설정

django-ninja API 테스트는 `ninja.testing.TestClient`를 사용한다:

```python
from ninja.testing import TestClient
from todos.urls import api

client = TestClient(api)
```

인증이 필요한 엔드포인트는 `TestClient`에 사용자 객체를 직접 주입한다:

```python
response = client.get("/todos/", user=member)
```

### 2. 테스트 클래스 구조

각 엔드포인트별로 `TestCase` 클래스를 분리하고, `setUp`에서 공통 픽스처를 생성한다:

```python
from django.test import TestCase
from accounts.models import Member
from todos.models import Todo, Category

class TodoListTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create_user(
            username="testuser", password="testpass"
        )
        self.todo = Todo.objects.create(
            member=self.member, title="테스트 할일"
        )
```

### 3. 검증 항목

각 엔드포인트 테스트에서 반드시 검증해야 할 항목:

- **상태 코드**: `assertEqual(response.status_code, 200)`
- **응답 데이터 형식**: 목록은 `list`, 단건은 `dict`
- **데이터 정확성**: 생성/수정된 값이 응답에 올바르게 반영되는지
- **권한 격리**: 다른 사용자의 데이터에 접근 불가 (404 반환)
- **필터링**: 쿼리 파라미터(`?status=`)가 올바르게 동작하는지

### 4. Todo API 테스트 시나리오

`todos/tests.py`에 아래 시나리오를 모두 커버한다:

#### 정상 케이스 (Happy Path)

| 클래스 | 시나리오 |
|--------|----------|
| `TodoListTest` | 목록 조회, status 필터, 타인 데이터 미노출 |
| `TodoCreateTest` | 생성 성공(카테고리 없음/있음) |
| `TodoDetailTest` | 상세 조회 성공 |
| `TodoUpdateTest` | PUT 전체 수정 성공 |
| `TodoPatchTest` | PATCH 부분 수정, 수정 안 한 필드 유지 확인 |
| `TodoDeleteTest` | 삭제 성공(204 반환, DB에서 실제 삭제 확인) |

#### 예외/실패 케이스 (Edge Cases & Error Handling)

다음 실패 시나리오를 **반드시** 테스트 클래스마다 포함한다:

| 시나리오 | 기대 동작 |
|----------|-----------|
| 타인 할일 조회 | 404 반환 |
| 타인 할일 수정(PUT/PATCH) | 404 반환 |
| 타인 할일 삭제 | 404 반환 |
| 존재하지 않는 `todo_id` 조회/수정/삭제 | 404 반환 |
| 타인 소유 카테고리로 Todo 생성 | 404 반환 |
| 타인 소유 카테고리로 Todo 수정 | 404 반환 |
| 존재하지 않는 카테고리 ID로 생성/수정 | 404 반환 |
| 필수 필드(`title`) 누락하여 생성 | 422 반환 |
| 잘못된 `status` 값으로 필터 | 빈 목록 반환 (에러 아님) |

각 예외 케이스는 독립 메서드로 분리한다. 예:

```python
def test_타인_할일_조회시_404(self):
    response = client.get(f"/todos/{other_todo.id}/", user=self.member)
    self.assertEqual(response.status_code, 404)

def test_존재하지_않는_todo_조회시_404(self):
    response = client.get("/todos/99999/", user=self.member)
    self.assertEqual(response.status_code, 404)

def test_타인_카테고리로_생성시_404(self):
    response = client.post("/todos/", json={"title": "테스트", "category": other_category.id}, user=self.member)
    self.assertEqual(response.status_code, 404)

def test_필수_필드_누락시_422(self):
    response = client.post("/todos/", json={}, user=self.member)
    self.assertEqual(response.status_code, 422)
```

### 5. 테스트 실행 명령

```sh
uv run python manage.py test todos          # todos 앱 테스트만
uv run python manage.py test accounts       # accounts 앱 테스트만
uv run python manage.py test                # 전체 테스트
```

## 작업 절차

1. 대상 앱의 `tests.py` 파일을 읽어 기존 테스트 확인
2. 해당 앱의 `models.py`, `views.py`, `schemas.py`를 읽어 테스트 범위 파악
3. 위 규칙에 따라 정상 케이스 + 예외/실패 케이스를 모두 포함한 테스트 코드 작성
4. `uv run python manage.py test <앱이름>`으로 테스트 실행 및 통과 확인
5. 실패 시 오류 메시지를 분석하고 수정

## 주의사항

- `TestClient`는 미들웨어를 거치지 않으므로 `user=` 인자로 인증을 직접 주입한다
- `unique_together = [member, name]` 제약으로 인해 같은 사용자의 카테고리명은 중복 불가
- `Todo.member`는 `SET_NULL`이므로 삭제 테스트 후 `null` 처리 주의
- 예외 케이스 테스트에서는 다른 사용자(`other_member`)를 `setUp`에서 함께 생성한다
- 모든 주석과 테스트 메서드명 설명은 한국어로 작성한다
