# API 문서

django-ninja 기반 REST API. 루트 URL `/api/`에 마운트된다.

## 인증

모든 엔드포인트는 로그인된 사용자(`request.user`)의 데이터만 접근한다.

## Todos

기본 경로: `/api/todos/`

### 스키마

| 클래스 | 용도 |
|--------|------|
| `TodoCreate` | 생성(POST) / 전체 수정(PUT) 요청 바디 |
| `TodoPatch` | 부분 수정(PATCH) 요청 바디 — 모든 필드 Optional |
| `TodoList` | 응답 (id, title, description, status, category, member) |

### 엔드포인트

| 메서드 | 경로 | 응답 코드 | 설명 |
|--------|------|-----------|------|
| GET | `/` | 200 | 목록 조회 (`?status=`로 필터 가능) |
| POST | `/` | 201 | 생성 |
| GET | `/{todo_id}/` | 200 | 상세 조회 |
| PUT | `/{todo_id}/` | 200 | 전체 수정 |
| PATCH | `/{todo_id}/` | 200 | 부분 수정 |
| DELETE | `/{todo_id}/` | 204 | 삭제 |

category 지정 시 해당 카테고리도 `member=request.user` 소유 여부를 검증한다.
