# todos 앱

할일(Todo) 관리 핵심 앱. Category로 할일을 분류하고, django-ninja 기반 REST API를 제공한다.

## 모델

### Category
- `member` (FK → Member, CASCADE) — 카테고리 소유자
- `name` (CharField, max=50) — 카테고리 이름
- 제약: `unique_together = [member, name]`

### Todo
- `member` (FK → Member, SET_NULL, nullable) — 할일 소유자
- `category` (FK → Category, SET_NULL, nullable) — 카테고리
- `title` (CharField, max=200) — 제목
- `description` (TextField, blank) — 설명
- `status` (CharField) — 상태값: `todo`, `in_progress`, `done`

## API 엔드포인트

기본 경로: `/api/todos/`

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 목록 조회 (`?status=`로 필터 가능) |
| POST | `/` | 생성 |
| GET | `/{todo_id}/` | 상세 조회 |
| PUT | `/{todo_id}/` | 전체 수정 |
| PATCH | `/{todo_id}/` | 부분 수정 |
| DELETE | `/{todo_id}/` | 삭제 (204) |

모든 엔드포인트는 `member=request.user`로 본인 데이터만 접근한다.

## 파일 구조

- `models.py` — Category, Todo 모델
- `schemas.py` — TodoIn(생성/전체수정), TodoPatch(부분수정), TodoOut(응답) 스키마
- `views.py` — django-ninja Router로 CRUD 엔드포인트 정의
- `urls.py` — NinjaAPI 인스턴스 생성 및 router 마운트
