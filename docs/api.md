# API 문서

django-ninja 기반 REST API. 루트 URL `/api/`에 마운트된다.

## 인증

모든 엔드포인트는 로그인된 사용자(`request.user`)의 데이터만 접근한다.

## Accounts

기본 경로: `/api/accounts/`

### 스키마

| 클래스 | 용도 |
|--------|------|
| `MemberSignupIn` | 회원가입(POST) 요청 바디 |
| `MemberUpdateIn` | 정보 수정(PATCH) 요청 바디 — 모든 필드 Optional (이름/이메일만 수정 가능, 비밀번호 변경은 별도 플로우) |
| `MemberOut` | 응답 (id, username, email, first_name, last_name, date_joined — password 미포함) |

### 엔드포인트

| 메서드 | 경로 | 인증 | 응답 코드 | 설명 |
|--------|------|------|-----------|------|
| POST | `/signup/` | 불필요 | 201 / 400 | 회원가입. 비밀번호 확인 불일치, 아이디/이메일 중복 시 400 |
| GET | `/me/` | 필요 | 200 | 내 정보 조회 |
| PATCH | `/me/` | 필요 | 200 / 400 | 내 정보 수정 (이메일 중복 시 400) |
| DELETE | `/me/` | 필요 | 204 | 회원 탈퇴 (soft-delete) |

### 회원 탈퇴 정책

탈퇴는 `is_active=False`로 바꾸는 soft-delete다. 이때 `username`/`email`을 `NULL`로 비운다 — Django의 `USERNAME_FIELD`(`username`)는 전역 `unique=True`가 필수라 값을 남겨두면 동일 아이디 재가입이 막히기 때문. NULL은 unique 제약에서 제외되므로, 탈퇴한 계정과 같은 username/email로 재가입이 가능하다. 단, 재가입은 완전히 새로운 `Member` row(새 PK)로 생성되며 탈퇴 전 소유했던 `Todo`/`Category` 데이터와는 연결되지 않는다.

`email`은 값이 비어있지 않고(`""` 아님) NULL도 아닌 경우에만 유일성을 검사한다(조건부 unique constraint) — 이메일 없이 생성된 계정끼리는 충돌하지 않는다.

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

### Categories

기본 경로: `/api/todos/categories/`

#### 스키마

| 클래스 | 용도 |
|--------|------|
| `CategoryCreate` | 생성(POST) 요청 바디 (name) |
| `CategoryPatch` | 부분 수정(PATCH) 요청 바디 — name Optional |
| `CategoryOut` | 응답 (id, name, member) |

#### 엔드포인트

| 메서드 | 경로 | 응답 코드 | 설명 |
|--------|------|-----------|------|
| GET | `/` | 200 | 목록 조회 |
| POST | `/` | 201 / 400 | 생성. 같은 회원 내 이름 중복 시 400 |
| GET | `/{category_id}/` | 200 | 상세 조회 |
| PATCH | `/{category_id}/` | 200 / 400 | 부분 수정. 이름 중복 시 400 |
| DELETE | `/{category_id}/` | 204 | 삭제 |

`member`가 다른 카테고리에 접근하면 404를 반환한다(존재 여부를 노출하지 않음). 이름 유일성은 회원 단위로 검증한다(`unique_together = [member, name]`).
