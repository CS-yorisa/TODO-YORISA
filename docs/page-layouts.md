# 페이지 레이아웃

각 페이지의 URL, 템플릿 경로, 섹션 구성, 사용된 HTMX 패턴을 정리합니다.

---

## 메인 페이지 (랜딩)

회원가입/로그인 이전에 보여지는 서비스 소개 페이지입니다. 로그인 상태에 따라 헤더 내비게이션이 변경됩니다.

- URL: `/`
- 뷰: `yorisa/urls.py` > `index()`
- 템플릿: `templates/index.html`
- 파셜: `templates/components/index/feature_todo.html`, `feature_points.html`, `feature_shop.html`

### 섹션 구성

| 순서 | 섹션 | 설명 |
|------|------|------|
| 1 | Header | 로고, 로그인 상태에 따라 로그인/회원가입 또는 사용자 이름/로그아웃 표시 (sticky) |
| 2 | Hero | 서비스 소개 문구 + TODO 미리보기 카드 |
| 3 | Features | 클라이언트 사이드 JS 탭으로 전환되는 3가지 기능 소개 (할 일 관리, 포인트 시스템, 재료 상점) |
| 4 | Stats | 서비스 통계 수치 4개 (완료된 할 일, 적립된 포인트, 구매된 재료, 활성 사용자) |
| 5 | CTA | 회원가입 유도 + 첫 가입 100p 혜택 안내 |
| 6 | Footer | 로고, 저작권 표시 |

### 탭 전환

세 파셜(`feature_todo.html`, `feature_points.html`, `feature_shop.html`)을 모두 `{% include %}`로 렌더링 시 함께 포함하고, `static/js/index.js`의 `setActiveTab()`이 `data-panel` 속성을 기준으로 `.feature-panel-wrap--hidden` 클래스를 토글해 화면에 보이는 패널만 전환합니다. 서버 왕복 없이 클라이언트에서만 처리됩니다 (HTMX 미사용).

---

## 회원가입 페이지

일반 사용자 회원가입 폼 페이지입니다. 가입 완료 시 로그인 페이지로 이동합니다.

- URL: `/accounts/signup/`
- 뷰: `accounts/views.py` > `signup()`
- 템플릿: `templates/accounts/signup.html`

### 섹션 구성

| 순서 | 섹션 | 설명 |
|------|------|------|
| 1 | Auth Card | 로고, 제목, 설명, 회원가입 폼 (성, 이름, 아이디, 이메일, 비밀번호, 비밀번호 확인), 로그인 링크 |

---

## 로그인 페이지

사용자 로그인 폼 페이지입니다. 로그인 완료 시 메인 페이지로 이동하며 세션이 유지됩니다.

- URL: `/accounts/login/`
- 뷰: `accounts/views.py` > `login()`
- 템플릿: `templates/accounts/login.html`

### 섹션 구성

| 순서 | 섹션 | 설명 |
|------|------|------|
| 1 | Auth Card | 로고, 제목, 설명, 로그인 폼 (아이디, 비밀번호), 회원가입 링크 |

---

## 로그아웃

별도 페이지 없이 세션 해제 후 메인 페이지로 리다이렉트합니다.

- URL: `/accounts/logout/`
- 뷰: `accounts/views.py` > `logout()`
- 템플릿: 없음 (리다이렉트)

---

## 할 일 목록 페이지

로그인한 사용자의 할 일을 카테고리별로 조회·관리하는 페이지입니다. 카테고리 사이드바와 할 일 리스트로 구성되며, 대부분의 상호작용이 HTMX로 처리됩니다.

- URL: `/todos/`
- 뷰: `todos/views.py` > `todo_list()`
- 템플릿: `templates/todos/list.html`
- 파셜: `templates/todos/components/category_list.html`, `todo_section.html`, `todo_items.html`, `todo_card.html`

### 섹션 구성

| 순서 | 섹션 | 설명 |
|------|------|------|
| 1 | Header | 로고만 표시 (sticky) |
| 2 | Category Sidebar | 카테고리 목록(`category_list.html`), 편집 모드 토글, 선택 삭제 바, 새 카테고리 추가 폼 |
| 3 | Todo Section | 할 일 추가 폼, 상태 필터 탭, 선택 삭제 버튼, 할 일 카드 리스트(`todo_section.html` > `todo_items.html` > `todo_card.html`) |

### HTMX 사용

| 동작 | 엔드포인트 | 파셜 템플릿 |
|------|-----------|-------------|
| 카테고리/상태 필터로 할 일 목록 조회 | `GET /todos/` (`HX-Request` 헤더) | `todos/components/todo_section.html` 또는 `todos/components/todo_items.html` (`HX-Target`에 따라 분기) |
| 할 일 생성 | `POST /todos/create/` | `todos/components/todo_items.html` (OOB로 `category_list.html` 갱신 포함) |
| 할 일 상태 변경 | `POST /todos/<id>/status/` | `todos/components/todo_card.html` |
| 할 일 카테고리 변경 | `POST /todos/<id>/category/` | `todos/components/todo_card.html` |
| 할 일 마감일 변경 | `POST /todos/<id>/due-date/` | `todos/components/todo_card.html` |
| 할 일 선택 삭제 | `POST /todos/delete/` | `todos/components/todo_items.html` (OOB로 `category_list.html` 갱신 포함) |
| 카테고리 이름 수정 | `POST /todos/categories/<id>/update/` | `todos/components/category_list.html` |
| 카테고리 선택 삭제 | `POST /todos/categories/delete/` | `todos/components/category_list.html` |

카테고리 생성(`POST /todos/categories/create/`)은 HTMX가 아닌 일반 폼 제출로 처리되어 `todo_list` URL로 리다이렉트됩니다.

---

## 기능 탭 파셜

메인 페이지 Features 섹션에서 클라이언트 사이드 탭 전환으로 표시되는 파셜 템플릿입니다. 독립 페이지가 아니며 별도 URL/뷰 없이 `index()` 렌더링 시 한 번에 모두 포함됩니다.

| 탭 키 | 파셜 템플릿 | 설명 |
|-------|------------|------|
| `todo` | `templates/components/index/feature_todo.html` | 스마트 할 일 관리 소개 + 미니 TODO 카드 |
| `points` | `templates/components/index/feature_points.html` | 포인트 시스템 소개 + 포인트 히스토리 카드 |
| `shop` | `templates/components/index/feature_shop.html` | 재료 상점 소개 + 상점 그리드 카드 |

---

## 공통 디자인 테마

| CSS 변수 | 색상 | 용도 |
|----------|------|------|
| `--primary` | `#2D6A4F` | 메인 초록 |
| `--primary-light` | `#52B788` | 밝은 초록 (포커스, 체크) |
| `--primary-dark` | `#1B4332` | 진한 초록 (제목, 호버) |
| `--accent` | `#F4A261` | 오렌지 강조 |
| `--accent-dark` | `#E76F51` | 진한 오렌지 (포인트 표시) |
| `--bg` | `#FEFAE0` | 크림 배경 |
| `--bg-alt` | `#F0F4EF` | 대체 배경 (섹션 구분) |
| `--bg-card` | `#FFFFFF` | 카드 배경 |

반응형: `768px` 이하 (태블릿/모바일), `480px` 이하 (소형 모바일)
