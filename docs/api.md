# API 문서

django-ninja 기반 REST API. 루트 URL `/api/`에 마운트된다.

## 인증

Todos API 등 기존 엔드포인트는 로그인된 사용자(`request.user`)의 데이터만 접근한다(세션 기반, 현재 JWT 미적용).

## 요청 횟수 제한

비밀번호 무작위 대입과 메일 폭탄을 막기 위해 일부 엔드포인트에 django-ninja throttle을 적용한다. 초과하면 **429** `{"detail": "Too many requests."}`를 반환한다.

| 엔드포인트 | 제한 | 기준 |
|------------|------|------|
| `POST /api/auth/login/` | 10회/분 | IP |
| `POST /api/auth/password/reset/` | 5회/시간 | IP |
| `POST /api/accounts/me/verify-password/` | 5회/분 | 회원 |

- 비율은 `settings.NINJA_DEFAULT_THROTTLE_RATES`에서 바꾼다. 엔드포인트마다 scope가 달라 서로의 횟수를 나눠 쓰지 않는다.
- IP는 `REMOTE_ADDR`로 식별한다(`NINJA_NUM_PROXIES=0`). 프록시 뒤에 배포하면 `.env`의 `NINJA_NUM_PROXIES`에 프록시 수를 지정해야 한다. 지정하지 않으면 모든 요청이 프록시 IP 하나로 묶인다.
- 재설정 메일은 추가로 **같은 계정에 5분에 한 번**만 보낸다(`PASSWORD_RESET_EMAIL_COOLDOWN`). 응답은 항상 같은 202다.
- 요청 기록은 Django 캐시에 저장한다. 기본 캐시(LocMemCache)는 프로세스별이므로, 운영에서 워커를 여러 개 띄우면 Redis 같은 공유 캐시를 `CACHES`에 설정해야 제한이 정확하다.

## Auth

기본 경로: `/api/auth/`

PyJWT 기반 회원가입/로그인 API. 서명 알고리즘은 HS256, 서명 키는 `SECRET_KEY`를 재사용한다.

- Access 토큰 수명: 30분
- Refresh 토큰 수명: 7일
- 재확인(reauth) 토큰 수명: 10분 — 아래 [비밀번호 재확인](#비밀번호-재확인) 참고

`accounts.auth.JWTAuth`(`HttpBearer` 구현체)는 현재 회원 API(`/api/accounts/`)에 세션 인증과 함께 적용되어 있다. `Authorization: Bearer <access>` 헤더로 인증한다.

### 스키마

| 클래스 | 용도 |
|--------|------|
| `SignupIn` | 회원가입 요청 바디 (username, email, nickname, password) |
| `LoginIn` | 로그인 요청 바디 (username, password) |
| `RefreshIn` | 토큰 갱신 요청 바디 (refresh) |
| `MemberOut` | 회원가입 응답 (id, username, email, nickname) |
| `TokenOut` | 로그인 응답 (access, refresh) |
| `AccessOut` | 토큰 갱신 응답 (access) |
| `PasswordResetIn` | 비밀번호 재설정 메일 요청 바디 (username, email) |
| `PasswordResetConfirmIn` | 비밀번호 재설정 요청 바디 (uid, token, new_password) |
| `MessageOut` | 안내 메시지 응답 (detail) |
| `ErrorOut` | 에러 응답 (detail) |

### 엔드포인트

| 메서드 | 경로 | 응답 코드 | 설명 |
|--------|------|-----------|------|
| POST | `/signup/` | 201 | 회원가입(username, email, nickname, password). username 또는 email 중복 시 409, 이메일 형식 오류·비밀번호 정책 위반 시 400 |
| POST | `/login/` | 200 | 로그인, access/refresh 토큰 발급. 인증 실패 시 401 |
| POST | `/refresh/` | 200 | refresh 토큰으로 access 토큰 재발급. 토큰 무효/만료 시 401 |
| POST | `/password/reset/` | 202 | 아이디·이메일(대소문자 무시)이 일치하는 활성 회원에게 재설정 링크 메일 발송. 계정 존재 여부가 드러나지 않도록 **항상 같은 202 응답** |
| POST | `/password/reset/confirm/` | 204 / 400 | 메일 링크의 uid·token으로 새 비밀번호 설정. 토큰 무효·만료·재사용, 비밀번호 정책 위반 시 400 |

### 비밀번호 찾기(재설정)

1. `/password/reset/`이 메일로 새 비밀번호 입력 화면 링크를 보낸다. 링크 경로는 `settings.PASSWORD_RESET_URL`(기본 `/accounts/password/reset/{uid}/{token}/`, `.env`로 변경 가능)이다.
2. 그 화면이 경로의 uid·token과 새 비밀번호를 `/password/reset/confirm/`으로 보낸다.

> 새 비밀번호 입력 화면은 아직 없다. 프론트엔드에서 위 경로로 화면을 만들어야 메일 링크가 동작한다. 화면 작업 목록은 [accounts-frontend-todo.md](accounts-frontend-todo.md) 참고.

토큰은 Django `default_token_generator`로 만든다. 비밀번호 해시가 바뀌면 무효화되므로 1회만 쓸 수 있고, 유효 시간은 `PASSWORD_RESET_TIMEOUT`(1시간)이다. 메일 발송 설정은 `.env`의 `EMAIL_URL`(미설정 시 콘솔 출력). 발송 실패는 응답에 드러내지 않고 로그로만 남긴다.

## Accounts

기본 경로: `/api/accounts/`

로그인된 회원 자신의 정보를 다루는 API. 두 가지 인증을 허용한다(`auth=[JWTAuth(), django_auth]`).

- **JWT**: `Authorization: Bearer <access>` 헤더. 외부 클라이언트용이며 CSRF 검사가 없다.
- **세션**: 웹 화면에서 로그인해 생긴 세션 쿠키. 쓰기 요청(POST/PATCH/DELETE)에는 `X-CSRFToken` 헤더가 필요하다.

`JWTAuth`를 먼저 두는 이유: `django_auth`는 CSRF 검사에 실패하면 다음 인증으로 넘어가지 않고 403을 반환하므로, 헤더가 없을 때 조용히 넘어가는 `JWTAuth`가 앞에 있어야 JWT 요청이 CSRF에 막히지 않는다.

### 스키마

| 클래스 | 용도 |
|--------|------|
| `PasswordVerifyIn` | 비밀번호 재확인 요청 바디 (password) |
| `ReauthOut` | 비밀번호 재확인 응답 (reauth_token) |
| `MemberUpdateIn` | 정보 수정(PATCH) 요청 바디 — 모든 필드 선택 입력 (닉네임/이메일만 수정 가능). `nickname`은 NOT NULL이라 null 전송 시 422 |
| `PasswordChangeIn` | 비밀번호 변경 요청 바디 (new_password) |
| `MemberOut` | 응답 (id, username, email, nickname — password 미포함) |

### 엔드포인트

| 메서드 | 경로 | 응답 코드 | 설명 |
|--------|------|-----------|------|
| GET | `/me/` | 200 | 내 정보 조회 |
| POST | `/me/verify-password/` | 200 / 400 | 현재 비밀번호 재확인. 성공 시 재확인 토큰 발급, 불일치 시 400 |
| PATCH | `/me/` | 200 / 400 / 403 / 409 / 422 | 내 정보 수정. **`X-Reauth-Token` 필요**(없거나 무효 시 403). 이메일 형식 오류 400, 이메일 중복 409, 닉네임 길이 위반·null 422 |
| POST | `/me/password/` | 204 / 400 / 403 | 비밀번호 변경. **`X-Reauth-Token` 필요**(없거나 무효 시 403). 비밀번호 정책 위반 400. 세션으로 호출하면 로그인 유지 |
| DELETE | `/me/` | 204 / 403 | 회원 탈퇴 (soft-delete). **`X-Reauth-Token` 필요**(없거나 무효 시 403). 세션으로 호출하면 로그아웃도 함께 처리 |

### 비밀번호 재확인

정보 수정, 비밀번호 변경, 회원 탈퇴는 현재 비밀번호를 한 번 더 확인해야 한다. 웹 화면 흐름(재확인 화면 → 수정 화면)을 그대로 지원하기 위해 단기 토큰을 쓴다.

1. `POST /me/verify-password/`로 현재 비밀번호를 보내면 `reauth_token`(JWT, `token_type="reauth"`, 10분)을 받는다.
2. `PATCH /me/`, `POST /me/password/`, `DELETE /me/` 호출 시 `X-Reauth-Token: <reauth_token>` 헤더를 붙인다.
3. 서버는 토큰의 서명·만료·타입과 **요청한 회원 본인의 토큰인지**를 확인한다. access 토큰이나 다른 회원의 토큰은 403.

클라이언트는 토큰을 재확인 화면에서 수정 화면으로 넘겨 쓰고(예: `sessionStorage`), 수정·변경에 성공하면 버리는 것을 권장한다. 서버는 토큰을 1회용으로 강제하지 않으므로, 유효 시간(10분) 안에는 같은 토큰을 다시 쓸 수 있다.

### 회원 탈퇴 정책

탈퇴는 `is_active=False`, `withdrawn_at=탈퇴 시각`으로 바꾸는 soft-delete다. 되돌릴 수 없으므로 [비밀번호 재확인](#비밀번호-재확인) 토큰이 필요하다. `JWTAuth`와 `/auth/refresh/`가 `is_active=True`인 회원만 통과시키므로, 탈퇴 즉시 기존에 발급된 access/refresh 토큰이 모두 무효화된다. 세션으로 호출했다면 로그아웃도 함께 된다.

탈퇴해도 `email`은 **그대로 보존**한다. 이메일 중복은 DB 제약(`unique_active_member_email`)으로 **탈퇴하지 않은 회원끼리만** 막으므로(`withdrawn_at IS NULL` 조건), 탈퇴한 계정과 같은 이메일로 재가입할 수 있다. 다만 `username`은 이 모델에서 nullable이 아니라서 탈퇴해도 비워지지 않는다 — **탈퇴한 계정과 동일한 아이디로는 재가입할 수 없다.**

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
