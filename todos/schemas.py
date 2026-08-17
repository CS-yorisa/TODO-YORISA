"""todos API 요청/응답 스키마.

설계 원칙
- 요청 스키마의 제약(길이·choices)은 `todos.models`의 모델 제약을 그대로 반영한다.
  `api.py`는 `full_clean()`을 호출하지 않으므로, 스키마가 유일한 검증 지점이다.
- PATCH 스키마는 모든 필드에 기본값을 주어 "필수 아님"으로 만들고,
  핸들러에서 `payload.dict(exclude_unset=True)`로 전송된 필드만 반영한다.
- `| None`(nullable)은 **모델 컬럼이 `null=True`인 필드에만** 붙인다.
  `exclude_unset=True`는 "보내지 않은 필드"만 걸러낼 뿐 "명시적으로 보낸 null"은
  걸러내지 못하므로, NOT NULL 컬럼에 `| None`을 붙이면 `{"title": null}` 같은
  요청이 DB NOT NULL 위반으로 이어진다.
"""

from datetime import date
from typing import Annotated

from ninja import Schema
from pydantic import StringConstraints

from todos.models import Todo

# 모델 제약과 1:1로 대응하는 문자열 타입 별칭.
# strip_whitespace는 템플릿 뷰(`views.py`의 `.strip()`)와 동작을 맞추기 위한 것으로,
# 앞뒤 공백 제거 후 길이를 검사한다(공백만 있는 입력은 min_length 위반으로 422).
CategoryName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)
]
TodoTitle = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]

# `Todo.Status.TODO`를 직접 참조하면 django-stubs가 없는 환경의 mypy가 TextChoices 멤버를
# `tuple[str, str]`로 오인해 assignment 오류를 낸다. 값으로 생성하면 런타임 결과는 동일하다
# (`Todo.Status("todo") is Todo.Status.TODO`).
DEFAULT_STATUS = Todo.Status("todo")


class CategoryCreate(Schema):
    name: CategoryName


class CategoryPatch(Schema):
    # 기본값은 exclude_unset=True 때문에 사용되지 않는 자리표시자다.
    name: CategoryName = ""


class CategoryOut(Schema):
    id: int
    name: str
    member_id: int | None


class TodoCreate(Schema):
    """생성(POST) / 전체 수정(PUT) 요청 바디."""

    title: TodoTitle
    description: str = ""
    status: Todo.Status = DEFAULT_STATUS
    category: int | None = None
    due_date: date | None = None


class TodoPatch(Schema):
    """부분 수정(PATCH) 요청 바디.

    모든 필드가 선택 입력이다. `category`와 `due_date`만 모델이 `null=True`이므로
    명시적 null을 "값 해제"로 받아들이고, 나머지는 null을 422로 거절한다.
    """

    title: TodoTitle = ""
    description: str = ""
    status: Todo.Status = DEFAULT_STATUS
    category: int | None = None
    due_date: date | None = None


class TodoList(Schema):
    """응답 스키마.

    `status`는 의도적으로 `str`로 둔다. 이번 수정 이전에 API로 저장된
    choices 밖 값이 DB에 남아 있으면, enum으로 선언할 경우 응답 검증 단계에서
    ValidationError가 발생해 조회 자체가 500이 된다(수신은 관대하게).
    """

    id: int
    title: str
    description: str
    status: str
    category_id: int | None
    member_id: int | None
    due_date: date | None
