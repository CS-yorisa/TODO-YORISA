# API 문서

django-ninja 기반 REST API. 루트 URL `/api/`에 마운트된다.

## 인증

Todos API 등 기존 엔드포인트는 로그인된 사용자(`request.user`)의 데이터만 접근한다(세션 기반, 현재 JWT 미적용).

## Auth

기본 경로: `/api/auth/`

PyJWT 기반 회원가입/로그인 API. 서명 알고리즘은 HS256, 서명 키는 `SECRET_KEY`를 재사용한다.

- Access 토큰 수명: 30분
- Refresh 토큰 수명: 7일

향후 보호가 필요한 API에는 `accounts.auth.JWTAuth`(`HttpBearer` 구현체)를 `Router(auth=JWTAuth())` 형태로 적용할 수 있다. `Authorization: Bearer <access>` 헤더로 인증한다.

### 스키마

| 클래스 | 용도 |
|--------|------|
| `SignupIn` | 회원가입 요청 바디 (username, email, password) |
| `LoginIn` | 로그인 요청 바디 (username, password) |
| `RefreshIn` | 토큰 갱신 요청 바디 (refresh) |
| `MemberOut` | 회원가입 응답 (id, username, email) |
| `TokenOut` | 로그인 응답 (access, refresh) |
| `AccessOut` | 토큰 갱신 응답 (access) |
| `ErrorOut` | 에러 응답 (detail) |

### 엔드포인트

| 메서드 | 경로 | 응답 코드 | 설명 |
|--------|------|-----------|------|
| POST | `/signup/` | 201 | 회원가입. username 또는 email 중복 시 409, 이메일 형식 오류·비밀번호 정책 위반 시 400 |
| POST | `/login/` | 200 | 로그인, access/refresh 토큰 발급. 인증 실패 시 401 |
| POST | `/refresh/` | 200 | refresh 토큰으로 access 토큰 재발급. 토큰 무효/만료 시 401 |

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
