# 템플릿 작성 규칙

여러 작성자가 템플릿을 만들면서 생긴 스타일 편차를 줄이기 위한 공통 규칙입니다.
새 템플릿을 작성하거나 기존 템플릿을 수정할 때 이 규칙을 따릅니다.

## 1. 파일 배치

| 위치                        | 용도                                                                           |
| --------------------------- | ------------------------------------------------------------------------------ |
| `templates/*.html`          | 최상위 페이지 (`{% extends "base.html" %}` 사용)                               |
| `templates/accounts/`       | 계정 관련 페이지                                                               |
| `templates/todos/`          | Todo 관련 페이지                                                               |
| `templates/partials/`       | HTMX 응답으로 반환되는 조각 템플릿. `{% extends %}` 없이 순수 HTML 조각만 포함 |
| `templates/partials/todos/` | Todo 도메인 파셜 (재사용 카드/리스트 단위)                                     |

파셜은 도메인별 하위 폴더로 묶습니다. 새 도메인 파셜이 2개 이상 생기면 `partials/<domain>/` 폴더를 만듭니다.

## 2. `{% load %}` 위치

`{% load %}` 태그는 항상 **파일 최상단**, `{% extends %}` 바로 다음 줄에 둡니다. `{% block %}` 내부에서 로드하지 않습니다.

```html
{% extends "base.html" %}
{% load static %}

{% block title %}...{% endblock %}
```

파셜처럼 `{% extends %}`가 없는 파일은 파일 첫 줄에 둡니다.

```html
{% load todo_extras %}
<div class="todo-card">...</div>
```

## 3. 속성(attribute) 줄바꿈

태그 하나를 한 줄로 썼을 때 **대략 100~120자를 넘으면** 속성마다 줄바꿈하고 4칸 들여쓰기를 사용합니다. 넘지 않으면 한 줄로 유지합니다.

```html
<!-- 짧으면 한 줄 -->
<a href="/" class="nav__logo">🍳 Todo Yorisa</a>

<!-- 길면 속성마다 줄바꿈 -->
<button
    class="tab-btn tab-btn--active"
    hx-get="/features/todo/"
    hx-target="#feature-content"
    hx-swap="innerHTML"
    hx-indicator="#feature-spinner"
    onclick="setActiveTab(this)"
    role="tab"
>
    📋 할 일 관리
</button>
```

`class` 안에 `{% if %}` 분기가 들어가 길어지는 경우도 같은 기준으로 판단합니다. 애매하면 줄바꿈하는 쪽을 택합니다.

## 4. JS 배치: 템플릿 전용 스크립트는 `static/js`로 분리

페이지 전용 상호작용 로직(`togglePicker`, `setActiveTab` 같은 헬퍼 함수)은 템플릿 안 `<script>` 블록에 두지 않고 `static/js/<도메인>.js`로 분리합니다.

- 파일: `static/js/todos.js`, `static/js/index.js` 등 페이지/도메인 단위로 분리
- 로드: 각 페이지 템플릿의 `{% block extra_head %}` 또는 body 하단에서 `{% static %}`으로 로드
- 인라인 `<script>` 블록은 서버에서 내려준 값을 JS 전역 변수로 넘기는 짧은 초기화 코드만 허용합니다 (예: `const currentCategoryId = {{ current_category_id }};`)

```html
{% block extra_head %}
{% load static %}
<link rel="stylesheet" href="{% static 'css/todos.css' %}">
{% endblock %}

{% block body %}
...
{% endblock %}

{% block extra_script %}
{% load static %}
<script src="{% static 'js/todos.js' %}"></script>
{% endblock %}
```

기존 `templates/todos/list.html` 하단의 대형 `<script>` 블록은 이 규칙에 따라 순차적으로 `static/js/todos.js`로 이전합니다 (즉시 전체 이전을 요구하지는 않되, 새로 추가/수정하는 함수는 반드시 분리된 파일에 작성).

## 5. 이벤트 바인딩

- 서버와 통신이 필요한 동작(HTMX 요청 이후 후처리 등): `hx-on::after-request` 등 HTMX 네이티브 속성 사용
- 순수 클라이언트 상호작용(토글, 활성 탭 표시 등): `onclick` 인라인 + `static/js`에 정의된 전역 함수 호출

두 방식을 섞어 같은 목적에 쓰지 않습니다 (예: 같은 종류의 토글 동작에 한쪽은 `onclick`, 다른 쪽은 `hx-on` 쓰지 않기).

## 6. CSRF 토큰

- HTMX 요청(`hx-post`, `hx-get` 등)은 `base.html`의 전역 `htmx:configRequest` 핸들러가 `X-CSRFToken` 헤더를 자동으로 주입하므로 폼에 `{% csrf_token %}`을 **넣지 않습니다**.
- 일반 `<form method="post">` (HTMX를 쓰지 않는 순수 폼 제출)에는 `{% csrf_token %}`을 명시적으로 넣습니다.

## 7. BEM 네이밍

클래스명은 `block__element--modifier` 형식을 따릅니다.

- Block: 컴포넌트 단위 (`todo-card`, `category-list`, `status-picker`)
- Element: `__`로 연결 (`todo-card__title`, `category-list__item`)
- Modifier: `--`로 연결, 상태/변형 표현 (`todo-card--done`, `category-list__item--active`)

버튼처럼 여러 modifier 조합이 필요한 경우에도 element에 새 modifier를 추가하는 방식을 유지하고, element 이름 자체를 modifier로 대체하지 않습니다 (`todo-card__tag--btn`처럼 역할이 다른 경우는 별도 element로 취급).

## 8. 빈 줄 / 공백

- 파일 시작 부분에 의미 없는 빈 줄을 두지 않습니다.
- 블록 사이 구분은 빈 줄 1개로 통일합니다.
- 들여쓰기는 4칸 스페이스로 통일합니다 (탭 금지).

## 9. 주석

- 템플릿 내 HTML 주석(`<!-- -->`)은 섹션 구분처럼 큰 단위에서만 사용합니다 (예: `<!-- Hero -->`, `<!-- Stats -->`).
- 코드가 스스로 설명되는 경우 주석을 달지 않습니다. 모든 주석은 한국어로 작성합니다 (`CLAUDE.md` 언어 규칙).
