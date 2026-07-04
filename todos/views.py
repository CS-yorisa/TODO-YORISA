from django.shortcuts import get_object_or_404
from ninja import Router

from todos.models import Category, Todo
from todos.schemas import TodoCreate, TodoList, TodoPatch
from dataclasses import dataclass
from datetime import date
from typing import Optional

from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import Todo

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



@dataclass
class MockCategory:
    id: int
    name: str
    todo_count: int = 0

    def __str__(self):
        return self.name


@dataclass
class MockTodo:
    id: int
    title: str
    status: str
    category: Optional[MockCategory] = None
    due_date: Optional[date] = None

    def get_status_display(self):
        return {'todo': '할 일', 'in_progress': '진행 중', 'done': '완료'}.get(self.status, self.status)


_CATEGORIES = [
    MockCategory(id=1, name='업무', todo_count=2),
    MockCategory(id=2, name='개인', todo_count=1),
    MockCategory(id=3, name='공부', todo_count=1),
]

_TODOS = [
    MockTodo(id=1, title='기획서 작성', status='todo', category=_CATEGORIES[0]),
    MockTodo(id=2, title='코드 리뷰', status='in_progress', category=_CATEGORIES[0]),
    MockTodo(id=3, title='운동하기', status='done', category=_CATEGORIES[1], due_date=date.today()),
    MockTodo(id=4, title='알고리즘 공부', status='todo', category=_CATEGORIES[2]),
    MockTodo(id=5, title='일기 쓰기', status='todo'),
]


def _context(category_id='', status_filter=''):
    todos = _TODOS
    if category_id:
        todos = [t for t in todos if t.category and str(t.category.id) == category_id]
    if status_filter:
        todos = [t for t in todos if t.status == status_filter]
    return {
        'todos': todos,
        'categories': _CATEGORIES,
        'total_count': len(_TODOS),
        'status_filter': status_filter,
        'current_category_id': category_id,
        'Status': Todo.Status,
    }


def _todo_by_id(todo_id):
    return next((t for t in _TODOS if t.id == todo_id), _TODOS[0])


def todo_list(request):
    category_id = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    ctx = _context(category_id, status_filter)
    hx_target = request.headers.get('HX-Target', '')
    if hx_target == 'todo-list':
        return render(request, 'partials/todos/todo_items.html', ctx)
    elif request.headers.get('HX-Request'):
        return render(request, 'partials/todos/todo_section.html', ctx)
    return render(request, 'todos/list.html', ctx)


@require_POST
def todo_create(request):
    category_id = request.POST.get('category_id', '')
    return render(request, 'partials/todos/todo_items.html', {**_context(category_id), 'show_oob': True})


@require_POST
def todo_status_update(request, todo_id):
    return render(request, 'partials/todos/todo_card.html', {
        'todo': _todo_by_id(todo_id),
        'Status': Todo.Status,
        'categories': _CATEGORIES,
    })


@require_POST
def todo_category_update(request, todo_id):
    return render(request, 'partials/todos/todo_card.html', {
        'todo': _todo_by_id(todo_id),
        'Status': Todo.Status,
        'categories': _CATEGORIES,
    })


@require_POST
def todo_delete(request):
    category_id = request.POST.get('category_id', '')
    return render(request, 'partials/todos/todo_items.html', {**_context(category_id), 'show_oob': True})


@require_POST
def todo_due_date_update(request, todo_id):
    return render(request, 'partials/todos/todo_card.html', {
        'todo': _todo_by_id(todo_id),
        'Status': Todo.Status,
        'categories': _CATEGORIES,
    })


@require_POST
def category_create(request):
    return redirect('todo_list')


def _category_list_context():
    return {
        'categories': _CATEGORIES,
        'total_count': len(_TODOS),
        'current_category_id': '',
    }


@require_POST
def category_update(request, category_id):
    return render(request, 'partials/todos/category_list.html', _category_list_context())


@require_POST
def category_delete(request):
    return render(request, 'partials/todos/category_list.html', _category_list_context())
