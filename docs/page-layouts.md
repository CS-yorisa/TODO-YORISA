# 페이지 레이아웃

각 페이지의 URL, 템플릿 경로, 섹션 구성, 사용된 HTMX 패턴을 정리합니다.

---

## 메인 페이지 (랜딩)

회원가입/로그인 이전에 보여지는 서비스 소개 페이지입니다. 로그인 상태에 따라 헤더 내비게이션이 변경됩니다.

- URL: `/`
- 뷰: `yorisa/urls.py` > `index()`
- 템플릿: `templates/index.html`
- 파셜: `templates/partials/feature_todo.html`, `feature_points.html`, `feature_shop.html`

### 섹션 구성

| 순서 | 섹션 | 설명 |
|------|------|------|
| 1 | Header | 로고, 로그인 상태에 따라 로그인/회원가입 또는 사용자 이름/로그아웃 표시 (sticky) |
| 2 | Hero | 서비스 소개 문구 + TODO 미리보기 카드 |
| 3 | Features | HTMX 탭으로 전환되는 3가지 기능 소개 (할 일 관리, 포인트 시스템, 재료 상점) |
| 4 | Stats | 서비스 통계 수치 4개 (완료된 할 일, 적립된 포인트, 구매된 재료, 활성 사용자) |
| 5 | CTA | 회원가입 유도 + 첫 가입 100p 혜택 안내 |
| 6 | Footer | 로고, 저작권 표시 |

### HTMX 사용

| 동작 | 엔드포인트 | 파셜 템플릿 |
|------|-----------|-------------|
| 할 일 관리 탭 클릭 | `GET /features/todo/` | `partials/feature_todo.html` |
| 포인트 시스템 탭 클릭 | `GET /features/points/` | `partials/feature_points.html` |
| 재료 상점 탭 클릭 | `GET /features/shop/` | `partials/feature_shop.html` |

초기 렌더링 시 `feature_todo.html`이 `{% include %}`로 포함된다. 탭 클릭 시 `hx-target="#feature-content"`, `hx-swap="innerHTML"`로 교체된다.

---

## 회원가입 페이지

일반 사용자 회원가입 폼 페이지입니다. `accounts:signup` 뷰는 폼을 렌더링만 하고, 제출은 JS `fetch`로 회원가입 API(`POST /api/accounts/signup/`)를 직접 호출한다. 가입 성공 시 로그인 페이지로 이동한다.

- URL: `/accounts/signup/`
- 뷰: `accounts/views.py` > `signup()` (GET 렌더링 전용)
- 템플릿: `templates/accounts/signup.html`

### 섹션 구성

| 순서 | 섹션 | 설명 |
|------|------|------|
| 1 | Auth Card | 로고, 제목, 설명, 에러 메시지 영역(`#signup-error`), 회원가입 폼 (성, 이름, 아이디, 이메일, 비밀번호, 비밀번호 확인), 로그인 링크 |

### API 연동

폼 `submit` 이벤트를 JS에서 가로채(`e.preventDefault()`) `POST /api/accounts/signup/`에 JSON으로 전송한다.

- 비밀번호/비밀번호 확인 불일치 시 API 호출 전 프론트에서 먼저 검증
- 아이디/이메일 중복 등 API가 400을 반환하면 `#signup-error`에 `detail` 메시지를 표시
- 201 성공 시 `accounts:login`으로 리다이렉트

---

## 로그인 페이지

사용자 로그인 폼 페이지입니다. `authenticate()`로 아이디/비밀번호를 검증하는 세션 기반 Django 뷰이며, 로그인 완료 시 메인 페이지로 이동하고 세션이 유지된다. 인증 실패 시 같은 페이지에 에러 메시지를 표시한다.

- URL: `/accounts/login/`
- 뷰: `accounts/views.py` > `login()`
- 템플릿: `templates/accounts/login.html`

### 섹션 구성

| 순서 | 섹션 | 설명 |
|------|------|------|
| 1 | Auth Card | 로고, 제목, 설명, 에러 메시지(`{{ error }}`, 인증 실패 시), 로그인 폼 (아이디, 비밀번호), 회원가입 링크 |

---

## 로그아웃

별도 페이지 없이 세션 해제 후 메인 페이지로 리다이렉트합니다.

- URL: `/accounts/logout/`
- 뷰: `accounts/views.py` > `logout()`
- 템플릿: 없음 (리다이렉트)

---

## 기능 탭 파셜

메인 페이지의 HTMX 탭에서 로드되는 파셜 템플릿입니다. 독립 페이지가 아닙니다.

- URL: `/features/<str:tab>/`
- 뷰: `yorisa/urls.py` > `feature_tab()`

| 탭 키 | 파셜 템플릿 | 설명 |
|-------|------------|------|
| `todo` | `templates/partials/feature_todo.html` | 스마트 할 일 관리 소개 + 미니 TODO 카드 |
| `points` | `templates/partials/feature_points.html` | 포인트 시스템 소개 + 포인트 히스토리 카드 |
| `shop` | `templates/partials/feature_shop.html` | 재료 상점 소개 + 상점 그리드 카드 |

---

## 할 일 목록 페이지

로그인한 회원의 할 일을 카테고리별/상태별로 관리하는 페이지입니다. 사이드바(카테고리)와 본문(할 일 카드 목록)으로 구성되며, 대부분의 상호작용이 HTMX로 처리된다.

- URL: `/todos/`
- 뷰: `todos/views.py` > `todo_list()`
- 템플릿: `templates/todos/list.html`
- 파셜: `templates/partials/todos/category_list.html`, `todo_section.html`, `todo_items.html`, `todo_card.html`

### 섹션 구성

| 순서 | 섹션 | 설명 |
|------|------|------|
| 1 | Header | 로고만 표시하는 간단한 헤더 |
| 2 | 카테고리 사이드바 | 카테고리 목록(`#category-list`), 편집 모드 토글, 선택 삭제, 새 카테고리 추가 폼 |
| 3 | 할 일 섹션(`#todo-section`) | 할 일 추가 카드, 상태별 필터 탭(전체/할 일/진행 중/완료), 선택 삭제, 할 일 카드 목록(`#todo-list`) |

### HTMX 사용

| 동작 | 엔드포인트 | 파셜 템플릿 |
|------|-----------|-------------|
| 카테고리 클릭(전체 보기) | `GET /api/todos/` → `#todo-section` | `partials/todos/todo_section.html` |
| 카테고리 클릭(개별) | `GET /api/todos/?category={id}` → `#todo-section` | `partials/todos/todo_section.html` |
| 카테고리 선택 삭제 | `POST /api/todos/categories/delete/` → `#category-list` | `partials/todos/category_list.html` |
| 카테고리 이름 수정 | `POST /api/todos/categories/{id}/update/` → `#category-list` | `partials/todos/category_list.html` |
| 상태 필터 탭 클릭 | `GET /api/todos/?category=&status=` → `#todo-list` | `partials/todos/todo_items.html` |
| 할 일 추가 | `POST /api/todos/create/` → `#todo-list` | `partials/todos/todo_items.html` |
| 할 일 선택 삭제 | `POST /api/todos/delete/` → `#todo-list` | `partials/todos/todo_items.html` |
| 할 일 상태 변경 | `POST /api/todos/{id}/status/` → `#todo-card-{id}` | `partials/todos/todo_card.html` |
| 할 일 카테고리 변경 | `POST /api/todos/{id}/category/` → `#todo-card-{id}` | `partials/todos/todo_card.html` |
| 할 일 기한 변경 | `POST /api/todos/{id}/due-date/` → `#todo-card-{id}` | `partials/todos/todo_card.html` |

카테고리 새 추가 폼(`POST /api/todos/categories/create/`)은 일반 폼 제출(HTMX 아님)로 동작한다. 날짜 선택은 `flatpickr` 라이브러리(CDN)를 사용한다.

---

## 공통 디자인 테마

| CSS 변수 | 색상 | 용도 |
|----------|------|------|
| `--primary` | `#2D6A4F` | 메인 초록 |
| `--primary-light` | `#52B788` | 밝은 초록 (포커스, 체크) |
| `--primary-dark` | `#1B4332` | 진한 초록 (제목, 호버) |
| `--accent` | `#F4A261` | 오렌지 강조 |
| `--accent-dark` | `#E76F51` | 진한 오렌지 (포인트 표시, 폼 에러) |
| `--bg` | `#FEFAE0` | 크림 배경 |
| `--bg-alt` | `#F0F4EF` | 대체 배경 (섹션 구분) |
| `--bg-card` | `#FFFFFF` | 카드 배경 |

반응형: `768px` 이하 (태블릿/모바일), `480px` 이하 (소형 모바일)
