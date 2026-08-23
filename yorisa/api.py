"""프로젝트 전역 API 조립 지점.

각 앱은 `api.py`에서 `Router`만 export하고, `NinjaAPI` 인스턴스 생성과
마운트는 이 파일에서만 수행한다. 앱 모듈은 이 파일을 import하지 않는다
(순환 import 방지).
"""

from ninja import NinjaAPI

from accounts.api import profile_router, router as auth_router
from todos.api import router as todos_router

api = NinjaAPI()

api.add_router("/auth/", auth_router)
api.add_router("/accounts/", profile_router)
api.add_router("/todos/", todos_router)
