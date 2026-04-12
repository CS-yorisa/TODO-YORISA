# 페이지 레이아웃

각 페이지의 URL, 템플릿 경로, 섹션 구성, 사용된 HTMX 패턴을 정리합니다.

---

## 메인 페이지 (랜딩)

회원가입/로그인 이전에 보여지는 서비스 소개 페이지입니다.

- URL: `/`
- 뷰: `yorisa/urls.py` > `index()`
- 템플릿: `templates/index.html`
- 파셜: `templates/partials/feature_todo.html`, `feature_points.html`, `feature_shop.html`

### 섹션 구성

| 순서 | 섹션 | 설명 |
|------|------|------|
| 1 | Header | Todo Yorisa 로고, 로그인/회원가입 버튼 (sticky) |
| 2 | Hero | 서비스 소개 문구 + TODO 미리보기 카드 |
| 3 | Features | HTMX 탭으로 전환되는 3가지 기능 소개 |
| 4 | Stats | 서비스 통계 수치 4개 |
| 5 | CTA | 회원가입 유도 + 첫 가입 100p 혜택 안내 |
| 6 | Footer | 로고, 저작권 표시 |

### HTMX 사용

Feature 탭이 HTMX로 동작합니다.

| 탭 | 엔드포인트 | 파셜 템플릿 |
|----|-----------|-------------|
| 할 일 관리 | `GET /features/todo/` | `partials/feature_todo.html` |
| 포인트 시스템 | `GET /features/points/` | `partials/feature_points.html` |
| 재료 상점 | `GET /features/shop/` | `partials/feature_shop.html` |

초기 렌더링 시 `feature_todo.html`이 `{% include %}`로 포함됩니다.

### 디자인 테마

| CSS 변수 | 색상 | 용도 |
|----------|------|------|
| `--primary` | `#2D6A4F` | 메인 초록 |
| `--primary-light` | `#52B788` | 밝은 초록 |
| `--accent` | `#F4A261` | 오렌지 강조 |
| `--accent-dark` | `#E76F51` | 진한 오렌지 |
| `--bg` | `#FEFAE0` | 크림 배경 |

반응형: `768px` 이하 (태블릿/모바일), `480px` 이하 (소형 모바일)
