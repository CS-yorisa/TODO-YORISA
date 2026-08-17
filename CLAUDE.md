# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 언어 규칙

- 모든 문서, 주석, 커밋 메시지는 한국어로 작성한다.

## 프로젝트 개요

Todo 요리사 ("할일을 맛있게 요리해 줍니다") - Django 6, Python 3.14 기반 할일 관리 웹 앱. 패키지 매니저로 uv 사용.

## 주요 명령어

```sh
uv sync                              # 의존성 설치
make dev                             # 개발 서버 실행 (uv run python manage.py runserver)
make shell                           # Django 셸
make makemigrations                  # 마이그레이션 생성
make migrate                         # 마이그레이션 적용
make check                           # ruff 린트 검사
make check-fix                       # ruff 린트 + 자동 수정
uv run mypy .                        # 타입 검사
make celery-worker                   # Celery 워커 실행
make celery-beat                     # Celery beat 스케줄러 실행
```

## 아키텍처

- **yorisa/** — Django 프로젝트 설정 (settings, 루트 URL 설정, `celery.py`에서 Celery app 초기화)
- **accounts/** — 커스텀 유저 모델 (`Member`, `AbstractUser` 상속). `AUTH_USER_MODEL = "accounts.Member"`. `tasks.py`에 Celery 백그라운드 작업 (자세한 내용은 [docs/celery.md](docs/celery.md))
- **todos/** — 핵심 앱: `Todo`, `Category` 모델 및 django-ninja REST API
- **templates/** — Django 템플릿 + HTMX. `base.html`에서 HTMX CDN 로드
- **static/** — 정적 파일 (CSS)
- **docs/** — ERD (`erd.md`), 페이지 레이아웃 (`page-layouts.md`), 템플릿 작성 규칙 (`template-conventions.md`), Celery (`celery.md`)

### API 계층

API는 **django-ninja**를 사용한다 (DRF 아님). 구조:
- `todos/urls.py`에서 `NinjaAPI` 인스턴스 생성 후 라우터 마운트
- `todos/views.py`에서 `@router.get/post/put/patch/delete`로 엔드포인트 정의
- `todos/schemas.py`에서 Pydantic 스타일 `Schema` 클래스로 요청/응답 검증
- 루트 URL 설정(`yorisa/urls.py`)에서 `/api/` 경로에 마운트

### 프론트엔드

Django 템플릿 + HTMX로 동적 콘텐츠 처리. `templates/index.html`을 서비스 진입점으로 삼고, 각 앱 페이지는 `templates/<app>/`(예: `templates/todos/`)에서 관리한다. 재사용 조각 템플릿(파셜/컴포넌트)은 해당 앱에서만 쓰이면 `templates/<app>/components/`, 여러 앱이 공유하면 `templates/components/`, `index.html` 전용이면 `templates/components/index/`에 둔다.

템플릿 작성 시 파일 배치, 속성 줄바꿈, `{% load %}` 위치, JS 배치, BEM 네이밍 등은 [docs/template-conventions.md](docs/template-conventions.md)를 따른다.

## 개발 규칙

- API 엔드포인트 개발 시 반드시 **django-ninja**를 사용한다 (DRF 사용 금지).
  - `Router`로 엔드포인트 정의 → `NinjaAPI` 인스턴스에 마운트
  - 요청/응답 검증은 `ninja.Schema` (Pydantic 기반) 사용
  - PATCH용 스키마는 모든 필드를 `Optional`로 선언하고 `exclude_unset=True`로 처리
- commit(커밋) 관련 요청이 오면 `commit` SKILL(`.claude/skills/commit/SKILL.md`)의 내용을 우선 참고하여 진행한다.

## 설정

- `django-environ`으로 환경변수 관리, 프로젝트 루트의 `.env` 파일에서 로드
- `SECRET_KEY`, `DEBUG`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`는 `.env`에서 읽음
- DB: SQLite (개발), PostgreSQL (운영 예정)
- Celery 브로커/결과 백엔드: Redis (로컬 개발 환경 실행 방법은 [docs/celery.md](docs/celery.md) 참고)
