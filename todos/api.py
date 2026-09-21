from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.security import django_auth

from todos.models import Category, Todo
from todos.schemas import (
    CategoryCreate,
    CategoryOut,
    CategoryPatch,
    TodoCreate,
    TodoList,
    TodoPatch,
)

router = Router(tags=["todos"], auth=django_auth)


def _apply_category(data: dict, request) -> None:
    """data 딕셔너리에 "category" 키가 있으면 소유권을 검증하고 "category_id"로 치환한다.

    `payload.dict()`(POST/PUT, 항상 "category" 키 존재)와
    `payload.dict(exclude_unset=True)`(PATCH, "category"가 없을 수 있음) 양쪽에서
    공용으로 쓴다. "category" 키가 없으면 아무 것도 하지 않는다.
    """
    if "category" not in data:
        return
    category_id = data.pop("category")
    if category_id is not None:
        get_object_or_404(Category, id=category_id, member=request.user)
    data["category_id"] = category_id


@router.get("/categories/", response=list[CategoryOut])
def category_list_api(request):
    return Category.objects.filter(member=request.user)


@router.post("/categories/", response={201: CategoryOut, 400: dict})
def category_create_api(request, payload: CategoryCreate):
    try:
        category = Category.objects.create(member=request.user, name=payload.name)
    except IntegrityError:
        return 400, {"detail": "이미 존재하는 카테고리 이름입니다."}
    return 201, category


@router.get("/categories/{category_id}/", response=CategoryOut)
def category_detail_api(request, category_id: int):
    return get_object_or_404(Category, id=category_id, member=request.user)


@router.patch("/categories/{category_id}/", response={200: CategoryOut, 400: dict})
def category_patch_api(request, category_id: int, payload: CategoryPatch):
    category = get_object_or_404(Category, id=category_id, member=request.user)

    data = payload.dict(exclude_unset=True)
    for attr, value in data.items():
        setattr(category, attr, value)

    try:
        category.save()
    except IntegrityError:
        return 400, {"detail": "이미 존재하는 카테고리 이름입니다."}

    return category


@router.delete("/categories/{category_id}/", response={204: None})
def category_delete_api(request, category_id: int):
    category = get_object_or_404(Category, id=category_id, member=request.user)
    category.delete()
    return 204, None


@router.get("/", response=list[TodoList])
def todo_list_api(request, status: Todo.Status | None = None):
    todos = Todo.objects.filter(member=request.user)
    if status:
        todos = todos.filter(status=status)
    return todos


@router.post("/", response={201: TodoList})
def todo_create_api(request, payload: TodoCreate):
    data = payload.dict()
    _apply_category(data, request)
    todo = Todo.objects.create(member=request.user, **data)
    return 201, todo


@router.get("/{todo_id}/", response=TodoList)
def todo_detail_api(request, todo_id: int):
    return get_object_or_404(Todo, id=todo_id, member=request.user)


@router.put("/{todo_id}/", response=TodoList)
def todo_update_api(request, todo_id: int, payload: TodoCreate):
    todo = get_object_or_404(Todo, id=todo_id, member=request.user)

    data = payload.dict()
    _apply_category(data, request)
    for attr, value in data.items():
        setattr(todo, attr, value)
    todo.save()
    return todo


@router.patch("/{todo_id}/", response=TodoList)
def todo_patch_api(request, todo_id: int, payload: TodoPatch):
    todo = get_object_or_404(Todo, id=todo_id, member=request.user)

    data = payload.dict(exclude_unset=True)
    _apply_category(data, request)

    for attr, value in data.items():
        setattr(todo, attr, value)
    todo.save()
    return todo


@router.delete("/{todo_id}/", response={204: None})
def todo_delete_api(request, todo_id: int):
    todo = get_object_or_404(Todo, id=todo_id, member=request.user)
    todo.delete()
    return 204, None
