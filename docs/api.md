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

## Accounts

기본 경로: `/api/accounts/`

로그인된 회원 자신의 정보를 다루는 API. `accounts.auth.JWTAuth`로 보호되며 `Authorization: Bearer <access>` 헤더가 필요하다.

### 스키마

| 클래스 | 용도 |
|--------|------|
| `MemberUpdateIn` | 정보 수정(PATCH) 요청 바디 — 모든 필드 Optional (이름/이메일만 수정 가능, 비밀번호 변경은 별도 플로우) |
| `MemberOut` | 응답 (id, username, email, first_name, last_name — password 미포함) |

### 엔드포인트

| 메서드 | 경로 | 응답 코드 | 설명 |
|--------|------|-----------|------|
| GET | `/me/` | 200 | 내 정보 조회 |
| PATCH | `/me/` | 200 / 409 | 내 정보 수정 (이메일 중복 시 409) |
| DELETE | `/me/` | 204 | 회원 탈퇴 (soft-delete) |

### 회원 탈퇴 정책

탈퇴는 `is_active=False`로 바꾸는 soft-delete다. `JWTAuth`가 `is_active=True`인 회원만 통과시키므로, 탈퇴 즉시 기존에 발급된 access/refresh 토큰이 모두 무효화된다.

탈퇴 시 `email`은 `None`으로 비운다 — `Member.email`은 nullable + unique이고 `save()`에서 빈 값을 `NULL`로 정규화하므로, 탈퇴한 계정과 같은 이메일로 재가입할 수 있다. 다만 `username`은 이 모델에서 nullable이 아니라서 탈퇴해도 비워지지 않는다 — **탈퇴한 계정과 동일한 아이디로는 재가입할 수 없다.**

## Todos

기본 경로: `/api/todos/`

### 스키마

| 클래스 | 용도 |
|--------|------|
| `TodoCreate` | 생성(POST) / 전체 수정(PUT) 요청 바디 |
| `TodoPatch` | 부분 수정(PATCH) 요청 바디 — 모든 필드 선택 입력 |
| `TodoList` | 응답 (id, title, description, status, category_id, member_id, due_date) |

#### 필드

| 필드 | 타입 | 제약 | `null` 허용 |
|------|------|------|-------------|
| `title` | string | 1~200자, 앞뒤 공백 제거 후 검사 | 불가 |
| `description` | string | 제한 없음 | 불가 |
| `status` | enum | `todo` / `in_progress` / `done` | 불가 |
| `category` | integer | 본인 소유 카테고리만 (아니면 404) | 허용 (값 해제) |
| `due_date` | string(date) | `YYYY-MM-DD` | 허용 (값 해제) |

PATCH에서 `category`·`due_date`에 `null`을 보내면 값이 해제된다. 나머지 필드에 `null`을 보내면 422다. 제약 위반은 모두 422를 반환한다.

### 엔드포인트

| 메서드 | 경로 | 응답 코드 | 설명 |
|--------|------|-----------|------|
| GET | `/` | 200 / 422 | 목록 조회 (`?status=`로 필터. 규격 밖 값은 422) |
| POST | `/` | 201 / 422 | 생성 |
| GET | `/{todo_id}/` | 200 | 상세 조회 |
| PUT | `/{todo_id}/` | 200 / 422 | 전체 수정 |
| PATCH | `/{todo_id}/` | 200 / 422 | 부분 수정 |
| DELETE | `/{todo_id}/` | 204 | 삭제 |

category 지정 시 해당 카테고리도 `member=request.user` 소유 여부를 검증한다.

**PUT은 전체 교체다.** 요청에서 생략한 필드는 모델 기본값으로 초기화된다 (`status`는 `todo`, `category`와 `due_date`는 `null`). 일부 필드만 바꾸려면 PATCH를 사용한다.

### Categories

기본 경로: `/api/todos/categories/`

#### 스키마

| 클래스 | 용도 |
|--------|------|
| `CategoryCreate` | 생성(POST) 요청 바디 (name — 1~50자, 앞뒤 공백 제거) |
| `CategoryPatch` | 부분 수정(PATCH) 요청 바디 — name 선택 입력, `null` 불가 |
| `CategoryOut` | 응답 (id, name, member_id) |

#### 엔드포인트

| 메서드 | 경로 | 응답 코드 | 설명 |
|--------|------|-----------|------|
| GET | `/` | 200 | 목록 조회 |
| POST | `/` | 201 / 400 / 422 | 생성. 같은 회원 내 이름 중복 시 400, 길이 위반 시 422 |
| GET | `/{category_id}/` | 200 | 상세 조회 |
| PATCH | `/{category_id}/` | 200 / 400 / 422 | 부분 수정. 이름 중복 시 400, 길이 위반 시 422 |
| DELETE | `/{category_id}/` | 204 | 삭제 |

`member`가 다른 카테고리에 접근하면 404를 반환한다(존재 여부를 노출하지 않음). 이름 유일성은 회원 단위로 검증한다(`unique_together = [member, name]`).
