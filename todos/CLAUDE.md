# todos 앱

할일(Todo) 관리 핵심 앱. Category로 할일을 분류하고, django-ninja 기반 REST API를 제공한다.

## 모델

### Category
- `member` (FK → Member, CASCADE, related_name="categories") — 카테고리 소유자
- `name` (CharField, max=50) — 카테고리 이름
- 제약: `unique_together = [member, name]`, `ordering = ["name"]`

### Todo
- `member` (FK → Member, SET_NULL, null=True, related_name="todos") — 할일 소유자
- `category` (FK → Category, SET_NULL, null=True, blank=True, related_name="todos") — 카테고리 (선택)
- `title` (CharField, max=200) — 제목
- `description` (TextField, blank=True) — 설명
- `status` (CharField, default="todo") — 상태값: `Todo.Status` TextChoices

#### Todo.Status
| 값            | 레이블  |
| ------------- | ------- |
| `todo`        | 할 일   |
| `in_progress` | 진행 중 |
| `done`        | 완료    |

## API

→ [docs/api.md](../docs/api.md) 참고

## 파일 구조

- `models.py` — Category, Todo 모델
- `schemas.py` — TodoCreate(생성/전체수정), TodoPatch(부분수정), TodoList(응답) 스키마
- `views.py` — 템플릿 렌더링 뷰 함수 (HTMX 파셜 포함)
- `api.py` — django-ninja Router로 CRUD 엔드포인트 정의, NinjaAPI 인스턴스 생성 및 router 마운트
- `urls.py` — 템플릿 뷰용 urlpatterns

## 테스트

→ [tests/CLAUDE.md](tests/CLAUDE.md) 참고
