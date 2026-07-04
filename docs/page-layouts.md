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

초기 렌더링 시 `feature_todo.html`이 `{% include %}`로 포함됩니다. 탭 클릭 시 `hx-target="#feature-content"`, `hx-swap="innerHTML"`로 교체됩니다.

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
