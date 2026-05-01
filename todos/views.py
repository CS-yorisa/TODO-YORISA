from django.shortcuts import get_object_or_404
from ninja import Router

from todos.models import Category, Todo
from todos.schemas import TodoCreate, TodoList, TodoPatch

router = Router(tags=["todos"])


@router.get("/", response=list[TodoList])
def todo_list(request, status: str | None = None):
    todos = Todo.objects.filter(member=request.user)
    if status:
        todos = todos.filter(status=status)
    return todos


@router.post("/", response={201: TodoList})
def todo_create(request, payload: TodoCreate):
    if payload.category is not None:
        get_object_or_404(Category, id=payload.category, member=request.user)

    data = payload.dict()
    data["category_id"] = data.pop("category")
    todo = Todo.objects.create(member=request.user, **data)
    return 201, todo


@router.get("/{todo_id}/", response=TodoList)
def todo_detail(request, todo_id: int):
    return get_object_or_404(Todo, id=todo_id, member=request.user)


@router.put("/{todo_id}/", response=TodoList)
def todo_update(request, todo_id: int, payload: TodoCreate):
    todo = get_object_or_404(Todo, id=todo_id, member=request.user)

    if payload.category is not None:
        get_object_or_404(Category, id=payload.category, member=request.user)

    data = payload.dict()
    data["category_id"] = data.pop("category")
    for attr, value in data.items():
        setattr(todo, attr, value)
    todo.save()
    return todo


@router.patch("/{todo_id}/", response=TodoList)
def todo_patch(request, todo_id: int, payload: TodoPatch):
    todo = get_object_or_404(Todo, id=todo_id, member=request.user)

    data = payload.dict(exclude_unset=True)
    if "category" in data and data["category"] is not None:
        get_object_or_404(Category, id=data["category"], member=request.user)
    if "category" in data:
        data["category_id"] = data.pop("category")

    for attr, value in data.items():
        setattr(todo, attr, value)
    todo.save()
    return todo


@router.delete("/{todo_id}/", response={204: None})
def todo_delete(request, todo_id: int):
    todo = get_object_or_404(Todo, id=todo_id, member=request.user)
    todo.delete()
    return 204, None
