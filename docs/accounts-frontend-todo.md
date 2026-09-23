# 회원 화면(HTML) 작업 요청

회원 API가 바뀌어서 화면 쪽 작업이 필요합니다. API는 모두 구현되어 있고, 명세는 [api.md](api.md)를 참고하세요.

핵심 변경은 두 가지입니다.

- 회원 이름이 **성/이름(`first_name`/`last_name`)에서 닉네임(`nickname`) 하나로** 바뀌었습니다.
- 정보 수정과 비밀번호 변경·찾기가 **API로 동작**합니다. 화면에서 `fetch`로 호출해야 합니다 (회원가입 화면과 같은 방식).

## 공통 사항

- 회원 API는 웹 로그인 세션으로 호출할 수 있습니다. 쓰기 요청(POST/PATCH/DELETE)에는 `X-CSRFToken` 헤더를 붙여 주세요.
- 에러 응답은 `{"detail": "메시지"}` 형태이고, `detail`을 그대로 화면에 보여주면 됩니다.
  - 단, 422(입력 형식 오류)는 `detail`이 배열이니 "입력값을 확인해 주세요." 같은 고정 문구를 보여주세요.

## 1. 회원가입 — 닉네임 입력란 추가 ⚠️ 급함

- 파일: `templates/accounts/signup.html`
- 닉네임 입력란을 추가하고, `/api/auth/signup/` 요청 바디에 `nickname`을 넣어 주세요.
- 닉네임은 **필수**, 앞뒤 공백 제거 후 **1~30자**입니다.
- **지금은 닉네임을 보내지 않아서 가입이 422로 실패합니다.**

```json
{"username": "...", "email": "...", "nickname": "요리왕", "password": "..."}
```

## 2. 헤더 — 닉네임 표시

- 파일: `templates/index.html`, `templates/todos/list.html`
- `{{ user.first_name|default:user.username }}`을 `{{ user.nickname|default:user.username }}`으로 바꿔 주세요.

## 3. 마이페이지 조회 — 닉네임 표시

- 파일: `templates/accounts/mypage.html`
- "이름" 항목의 `{{ profile.last_name }}{{ profile.first_name }}`을 "닉네임" / `{{ profile.nickname }}`으로 바꿔 주세요.
- `accounts/views.py`의 `mypage`는 아직 `MOCK_PROFILE`을 넘깁니다. 실제 회원을 보여주려면 `{"profile": request.user}`로 바꿔야 합니다.

## 4. 정보 수정 — 비밀번호 재확인 후 닉네임·이메일 수정

- 파일: `templates/accounts/mypage_verify.html`, `templates/accounts/mypage_edit.html`
- 수정 화면의 성/이름 입력란을 **닉네임 입력란 하나**로 바꿔 주세요.
- 흐름:
  1. **재확인 화면**: `POST /api/accounts/me/verify-password/` `{"password": "..."}`
     - 성공(200): `{"reauth_token": "..."}` → 토큰을 `sessionStorage` 등에 저장하고 수정 화면으로 이동
     - 실패(400): "비밀번호가 일치하지 않습니다."
  2. **수정 화면**: `PATCH /api/accounts/me/` `{"nickname": "...", "email": "..."}` + 헤더 `X-Reauth-Token: <토큰>`
     - 성공(200): 토큰을 버리고 마이페이지로 이동
     - 403: 토큰 없음·만료(10분) → 재확인 화면으로 돌려보내기
     - 400(이메일 형식 오류), 409(이메일 중복): `detail` 표시
- 수정 화면에 들어왔는데 저장된 토큰이 없으면 재확인 화면으로 보내 주세요.
- 이메일은 선택 입력이며, 빈 값으로 보내면 이메일이 지워집니다.

## 5. 비밀번호 변경 — 비밀번호 재확인 후 변경

- 파일: `templates/accounts/password_verify.html`, `templates/accounts/password_edit.html`
- 재확인은 4번과 같은 API(`/api/accounts/me/verify-password/`)를 씁니다.
- 변경: `POST /api/accounts/me/password/` `{"new_password": "..."}` + 헤더 `X-Reauth-Token: <토큰>`
  - 성공(204): 토큰을 버리고 마이페이지로 이동 (로그인은 유지됩니다)
  - 400: 비밀번호 정책 위반 → `detail` 표시
  - 403: 재확인 화면으로 돌려보내기
- "새 비밀번호 확인" 일치 검사는 화면에서 해 주세요 (지금 `static/js/accounts.js`에 있는 검사를 그대로 쓰면 됩니다).

## 6. 비밀번호 찾기 — 재설정 메일 요청

- 파일: `templates/accounts/password_find.html`
- `POST /api/auth/password/reset/` `{"username": "...", "email": "..."}`
- 계정이 있든 없든 항상 **202** `{"detail": "안내 문구"}`가 옵니다. `detail`을 성공 문구로 보여주면 됩니다 (계정 존재 여부가 드러나지 않게 하기 위함).

## 7. 새 비밀번호 입력 화면 — 신규 화면 필요

재설정 메일의 링크를 누르면 열리는 화면이 아직 없습니다.

- 메일 링크 경로: `/accounts/password/reset/<uid>/<token>/`
  - 경로는 `settings.PASSWORD_RESET_URL`로 정해져 있습니다. 다른 경로를 쓰려면 이 설정을 바꾸면 됩니다.
- 화면 구성: 새 비밀번호, 새 비밀번호 확인, 변경 버튼 (`password_edit.html`과 비슷)
- 제출: `POST /api/auth/password/reset/confirm/` `{"uid": "<경로의 uid>", "token": "<경로의 token>", "new_password": "..."}`
  - 성공(204): "비밀번호가 변경되었습니다. 새 비밀번호로 로그인해 주세요." + 로그인 링크
  - 400: 링크 만료(1시간)·이미 사용됨·비밀번호 정책 위반 → `detail` 표시
- 로그인 없이 접근하는 화면입니다. URL 등록과 뷰도 함께 필요합니다 (`accounts/urls.py`, `accounts/views.py`).

## 8. 회원 탈퇴 — 화면 만들 때 참고

지금 탈퇴 화면은 없습니다. 만든다면 탈퇴도 **비밀번호 재확인이 필요**합니다.

- 재확인(`/api/accounts/me/verify-password/`)으로 토큰을 받은 뒤 `DELETE /api/accounts/me/` + 헤더 `X-Reauth-Token: <토큰>`
  - 성공(204): 로그아웃된 상태가 되므로 메인 화면 등으로 이동
  - 403: 재확인 화면으로 돌려보내기

## 참고: 로컬에서 메일 확인

`.env`에 `EMAIL_URL`이 없으면 메일이 발송되지 않고 **개발 서버 콘솔에 출력**됩니다. 콘솔에 찍힌 링크로 7번 화면을 테스트할 수 있습니다.
