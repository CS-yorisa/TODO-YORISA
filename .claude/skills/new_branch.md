---
name: new-branch
description: 신기능 개발을 위한 새로운 브랜치를 생성합니다.
user_invocable: true
---

# 새 브랜치 생성

사용자에게 아래 정보를 순서대로 질문한 뒤, 브랜치를 생성합니다.

## 수집할 정보

1. **prefix**: `feature`, `fix`, `hotfix`, `docs` 중 하나를 선택하도록 질문
2. **AAA (모듈/도메인 이름)**: 자유 입력 (필수)
3. **issue 번호**: GitHub issue 번호 (선택 — 입력하지 않으면 생략)
4. **BBB (기능 이름)**: 자유 입력 (필수)

## 브랜치 이름 규칙

- issue 번호가 있는 경우: `{prefix}/{AAA}-#{issue}-{BBB}`
- issue 번호가 없는 경우: `{prefix}/{AAA}-{BBB}`

공백은 `-`로 치환하고, 소문자로 통일합니다.

## 실행 절차

1. 위 4가지 항목을 사용자에게 질문하여 값을 수집한다.
2. 브랜치 이름을 조합하여 사용자에게 확인을 요청한다.
3. 확인 후 `git switch -c {branch_name}` 명령으로 브랜치를 생성한다.
