# 마이페이지 백엔드 작업 목록

마이페이지(회원정보 조회/수정) 템플릿과 화면 미리보기용 URL/뷰는 만들어져 있지만,
`accounts/views.py`의 `mypage`, `mypage_verify`, `mypage_edit`는 **전부 목(mock) 데이터**로 동작합니다
(`MOCK_PROFILE` 상수 및 각 뷰의 `TODO` 주석 참고). 비밀번호 재확인도 실제로 검증하지 않고 통과시키며,
수정 폼도 실제로 저장하지 않습니다. 아래 내용대로 실제 회원 정보 조회/수정 API 연동 후 목 데이터를 제거해야 합니다.

## 완료된 템플릿

| 파일 | 역할 |
| --- | --- |
| `templates/accounts/mypage.html` | 회원정보 조회 화면 (아이디/이름/이메일 표시, "정보 수정"/"비밀번호 변경" 버튼) |
| `templates/accounts/mypage_verify.html` | 정보 수정 전 비밀번호 재확인 화면 |
| `templates/accounts/mypage_edit.html` | 회원정보 수정 폼 (성/이름/이메일) |
| `templates/accounts/password_verify.html` | 비밀번호 변경 전 비밀번호 재확인 화면 |
| `templates/accounts/password_edit.html` | 새 비밀번호 입력 폼 (새 비밀번호/새 비밀번호 확인) |
| `templates/accounts/password_find.html` | 로그인 화면의 "비밀번호가 기억나지 않으시나요?" → 비밀번호 찾기(아이디/이메일 입력) 화면 |

## 이미 만들어진 것 (임시 목 상태)

`accounts/urls.py`에 라우트 6개, `accounts/views.py`에 뷰 6개가 이미 있습니다.

```python
path("mypage/", views.mypage, name="mypage"),
path("mypage/verify/", views.mypage_verify, name="mypage_verify"),
path("mypage/edit/", views.mypage_edit, name="mypage_edit"),
path("mypage/password/verify/", views.password_verify, name="password_verify"),
path("mypage/password/edit/", views.password_edit, name="password_edit"),
path("password/find/", views.password_find, name="password_find"),
```

### 1. `mypage` — 회원정보 조회

- 현재: `MOCK_PROFILE`(하드코딩된 딕셔너리)을 `profile` 컨텍스트로 템플릿에 그대로 전달
- **바꿔야 할 것**: 실제 회원 정보 조회 API(또는 DB 조회) 결과를 `profile`에 담아 전달. 템플릿은 `profile.username`, `profile.last_name`, `profile.first_name`, `profile.email`을 참조하므로 같은 키 구조만 맞추면 템플릿 수정 없이 교체 가능

### 2. `mypage_verify` — 비밀번호 재확인

- 현재: `POST`가 오면 비밀번호를 검증하지 않고 무조건 `accounts:mypage_edit`로 통과시킴
- **바꿔야 할 것**: `request.POST["password"]`를 실제 비밀번호와 비교(`request.user.check_password()` 등)해서
  - 성공 시: 정보 수정이 가능하다는 상태를 세션 등에 기록하고 `accounts:mypage_edit`로 리다이렉트
  - 실패 시: `accounts/mypage_verify.html`을 `{"error": "비밀번호가 일치하지 않습니다."}` 컨텍스트로 다시 렌더링 (템플릿이 `{{ error }}`를 `form-error`로 표시함)

### 3. `mypage_edit` — 회원정보 수정

- 현재: `GET`은 `MOCK_PROFILE`로 폼을 채우고, `POST`는 저장 없이 바로 `accounts:mypage`로 리다이렉트
- **바꿔야 할 것**:
  - `mypage_verify`를 거치지 않고 직접 URL로 접근하면 `mypage_verify`로 되돌려보내는 가드 추가
  - `POST`로 온 `last_name`, `first_name`, `email`(선택)을 실제로 저장
  - 이메일 형식 검증 필요 (`django.core.validators.validate_email` 등)
  - `Member.email`은 `unique=True, null=True`이므로 중복 이메일 저장 시 `IntegrityError` 처리 필요 (`accounts/api.py`의 `update_me`, `signup` 참고)
  - 저장 성공 시 2번 단계에서 남긴 인증 상태를 해제 (수정할 때마다 비밀번호 재확인을 강제하기 위함)
  - 실패 시 `accounts/mypage_edit.html`을 `{"error": "..."}` 컨텍스트로 다시 렌더링

### 4. `password_verify` — 비밀번호 변경 전 본인 확인

- 현재: `POST`가 오면 비밀번호를 검증하지 않고 무조건 `accounts:password_edit`로 통과시킴
- **바꿔야 할 것**: `mypage_verify`와 동일한 방식으로 현재 비밀번호를 검증하고, 성공 시 (별도 세션 키 등으로) 인증 상태를 기록 후 `accounts:password_edit`로 리다이렉트

### 5. `password_edit` — 새 비밀번호 설정

- 현재: `POST`가 오면 저장 없이 바로 `accounts:mypage`로 리다이렉트. 새 비밀번호/확인 값 일치 여부는 `static/js/accounts.js`의 `password-edit-form` 제출 핸들러가 **클라이언트에서만** 검사함
- **바꿔야 할 것**:
  - `password_verify`를 거치지 않고 직접 URL로 접근하면 `password_verify`로 되돌려보내는 가드 추가
  - 서버에서도 `new_password` == `new_password_confirm` 재검증 (클라이언트 검사는 우회 가능)
  - `django.contrib.auth.password_validation.validate_password`로 비밀번호 정책 검증 (`accounts/api.py`의 `signup` 참고)
  - `request.user.set_password(new_password)` 후 저장, 세션 무효화 방지를 위해 `django.contrib.auth.update_session_auth_hash(request, request.user)` 호출 필요
  - 저장 성공 시 인증 상태 해제 후 `accounts:mypage`로 리다이렉트
  - 실패 시 `accounts/password_edit.html`을 `{"error": "..."}` 컨텍스트로 다시 렌더링 (템플릿의 `#password-edit-error`가 `{{ error }}`를 표시함)

### 6. `password_find` — 비밀번호 찾기 (로그인 화면에서 진입, 로그인 불필요)

- 현재: `@login_required`가 아님 (비로그인 상태에서 접근하는 화면이라 정상). `POST`가 오면 아이디/이메일 값을 검증하거나 실제 메일을 보내지 않고 무조건 `sent=True`로 같은 화면을 다시 렌더링해 성공 배너(`form-success`)만 보여줌
- **바꿔야 할 것**:
  - `request.POST`의 `username`, `email`이 실제로 일치하는 `Member`가 있는지 조회
  - 일치하는 계정이 있으면 비밀번호 재설정용 토큰(예: Django `PasswordResetTokenGenerator` 또는 자체 구현)을 발급하고, 그 토큰이 담긴 링크를 이메일로 발송
  - 토큰으로 접속했을 때 새 비밀번호를 입력받아 저장하는 화면/뷰도 별도로 필요 (현재 없음 — `password_edit`은 로그인 후 "본인이 현재 비밀번호를 아는 상태"에서 바꾸는 화면이라 용도가 다름)
  - 존재하지 않는 아이디/이메일이어도 계정 존재 여부가 유추되지 않도록 응답 문구는 항상 동일하게 유지할 것 (현재 템플릿의 "입력하신 이메일로 비밀번호 재설정 안내를 보내드렸습니다." 문구를 그대로 유지하면 됨)
  - 실패(입력값 누락 등) 시 `accounts/password_find.html`을 에러 컨텍스트로 다시 렌더링하는 처리 추가 검토

## 참고

- 로그인/회원가입/마이페이지 모두 세션 기반 인증(`django.contrib.auth`)을 쓰는 페이지이며, `accounts/api.py`의 JWT 기반 API(`profile_router`, `MemberUpdateIn`)와는 별개입니다. 다만 수정 가능한 필드(`last_name`, `first_name`, `email`)는 `MemberUpdateIn` 스키마와 동일하게 맞춰뒀습니다.
- 아이디(`username`)와 비밀번호는 이 화면에서 수정 대상이 아닙니다 (조회만 가능).
