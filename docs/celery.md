# Celery 백그라운드 작업

## 아키텍처

- **브로커**: Redis (`CELERY_BROKER_URL`, 기본 `redis://localhost:6379/0`)
- **결과 백엔드**: Redis (`CELERY_RESULT_BACKEND`, 기본 `redis://localhost:6379/1`). 결과는 디버깅 편의용이며 `CELERY_RESULT_EXPIRES`(1시간)로 짧게 만료된다. 결과를 영속화하거나 조회할 필요가 없어 `django-celery-results`는 사용하지 않는다.
- **스케줄 관리**: `yorisa/settings.py`의 `CELERY_BEAT_SCHEDULE`에서 코드로 관리한다. Admin에서 동적으로 스케줄을 바꿔야 하는 요구가 생기면 `django-celery-beat` 도입을 검토한다.
- Celery app은 `yorisa/celery.py`에서 초기화하고 `yorisa/__init__.py`에서 등록한다. 각 Django 앱의 `tasks.py`는 `autodiscover_tasks()`로 자동 탐색된다.

## 등록된 작업

### `accounts.tasks.detect_dormant_members`

`settings.DORMANT_MEMBER_DAYS`(기본 90일) 이상 미접속한 활성 회원(`is_active=True`, `withdrawn_at__isnull=True`)을 탐지해 로그(`INFO`)로 남긴다.

- `last_login`이 기준일 이전인 경우
- 한 번도 로그인하지 않은 경우(`last_login`이 NULL)는 `date_joined`가 기준일 이전인 경우에만 포함 (가입 직후 오탐 방지)

매일 1회(`CELERY_BEAT_SCHEDULE`) 실행되며, 이번 범위는 **탐지 후 로그만 남기는 것**까지다. 휴면 상태를 DB에 반영하거나 알림을 발송하는 기능은 아직 없다 (향후 확장 여지).

JWT 로그인(`accounts/api.py`의 `login`)은 성공 시 `Member.last_login`을 직접 갱신한다. 세션 로그인 경로는 `django.contrib.auth.login()`이 자동으로 갱신한다.

## 로컬 개발 환경

### Redis 실행

Docker:
```sh
docker run -d --name yorisa-redis -p 6379:6379 redis:7-alpine
```

Homebrew (macOS):
```sh
brew install redis
brew services start redis
```

확인:
```sh
redis-cli ping   # PONG
```

### worker / beat 실행

```sh
make celery-worker   # 별도 터미널
make celery-beat      # 별도 터미널
```

### 수동 실행 (shell)

```sh
make shell
```
```python
from accounts.tasks import detect_dormant_members
result = detect_dormant_members.apply()  # worker 없이 즉시 동기 실행
result.result  # 탐지된 회원 수
```
