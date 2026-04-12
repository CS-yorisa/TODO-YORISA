# HTMX 설정 가이드

## 1. HTMX 도입 방식

HTMX는 CDN을 통해 `templates/base.html`에서 전역으로 로드합니다.

```html
<script
    src="https://unpkg.com/htmx.org@2.0.4"
    integrity="sha384-HGfztofotfshcF7+8n44JQL2oJmowVChPTg48S+jvZoztPfvwD79OC/LTtG6dMp+"
    crossorigin="anonymous"
></script>
```

- 별도의 Python 패키지 설치 없이 프론트엔드에서 바로 사용
- 모든 페이지가 `base.html`을 상속하므로 HTMX가 전역 활성화됨

## 2. 템플릿 구조

### base.html

모든 페이지의 기본 골격입니다. 블록 구성:

| 블록 | 용도 |
|------|------|
| `{% block title %}` | 페이지 타이틀 |
| `{% block extra_head %}` | 페이지별 추가 head 태그 |
| `{% block body %}` | 페이지 본문 전체 |

### partials 디렉토리

HTMX 요청에 대한 응답으로 반환되는 HTML 조각(파셜)을 `templates/partials/`에 보관합니다.
파셜 템플릿은 `{% extends %}` 없이 순수 HTML 조각만 포함합니다.

## 3. 주요 HTMX 속성

| 속성 | 설명 | 예시 |
|------|------|------|
| `hx-get` | 서버에 GET 요청 | `hx-get="/my-endpoint/"` |
| `hx-post` | 서버에 POST 요청 | `hx-post="/submit/"` |
| `hx-target` | 응답을 삽입할 대상 요소 | `hx-target="#content"` |
| `hx-swap` | 대상 요소의 교체 방식 | `hx-swap="innerHTML"` |
| `hx-indicator` | 요청 중 표시할 로딩 인디케이터 | `hx-indicator="#spinner"` |
| `hx-trigger` | 요청을 트리거할 이벤트 | `hx-trigger="click"` |

## 4. 사용 패턴 예시

### 파셜 로드 (탭 전환)

```html
<!-- 트리거 버튼 -->
<button hx-get="/my-endpoint/" hx-target="#target-id" hx-swap="innerHTML">
    불러오기
</button>

<!-- 응답이 삽입될 대상 -->
<div id="target-id"></div>
```

### 로딩 인디케이터

HTMX는 요청 중 `htmx-request` 클래스를 자동으로 토글합니다. CSS에서 활용:

```css
.htmx-indicator { display: none; }
.htmx-request .htmx-indicator { display: block; }
```

### 뷰 함수 작성

파셜 뷰는 일반 Django 뷰와 동일하게 작성하되, 파셜 템플릿을 반환합니다:

```python
def my_partial(request):
    context = {"items": Item.objects.all()}
    return render(request, "partials/my_partial.html", context)
```

## 5. Static 파일 설정

`settings.py`:

```python
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
```

템플릿에서 사용:

```html
{% load static %}
<link rel="stylesheet" href="{% static 'css/main.css' %}">
```

## 6. 새로운 HTMX 파셜 추가 방법

1. `templates/partials/`에 HTML 파일 생성 (예: `partials/my_section.html`)
2. `yorisa/urls.py` (또는 앱 `urls.py`)에 뷰 함수 및 URL 패턴 추가
3. 기존 템플릿에서 `hx-get`, `hx-target`, `hx-swap` 속성으로 연결
