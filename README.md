## 개발 환경

- Python
- Django
- PostgrSQL

## 기술 스택

- python 3.14
- Django 6 (Django Template)
- uv (package manager)
- ruff (linter & formatter)

### 개발환경 설정

```sh
# uv 설치
# macOS & Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# python 라이브러리 설치
uv sync

# 개발 서버 시작
uv run ./manage.py runserver
# Makefile 사용
make dev
```

### 고민

- HTMX (Django template 에서 사용)
- django ninja (API 별도 기능 개발시)

## 개발 환경

- VSCode
  - 확장프로그램 목록
  - ruff (필수)
  - mypy (type checker)
- AI 활용?
  - ClaudeCode
  - Codex
  - ...