from datetime import date

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Count
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

from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import Todo

router = Router(tags=["todos"], auth=django_auth)


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



def _member_categories(member):
    return Category.objects.filter(member=member).annotate(todo_count=Count('todos'))


def _context(request, category_id='', status_filter=''):
    todos = Todo.objects.filter(member=request.user)
    if category_id:
        todos = todos.filter(category_id=category_id)
    if status_filter:
        todos = todos.filter(status=status_filter)
    return {
        'todos': todos,
        'categories': _member_categories(request.user),
        'total_count': Todo.objects.filter(member=request.user).count(),
        'status_filter': status_filter,
        'current_category_id': category_id,
        'Status': Todo.Status,
    }


@login_required
def todo_list(request):
    category_id = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    ctx = _context(request, category_id, status_filter)
    hx_target = request.headers.get('HX-Target', '')
    if hx_target == 'todo-list':
        return render(request, 'partials/todos/todo_items.html', ctx)
    elif request.headers.get('HX-Request'):
        return render(request, 'partials/todos/todo_section.html', ctx)
    return render(request, 'todos/list.html', ctx)


@login_required
@require_POST
def todo_create(request):
    title = request.POST.get('title', '').strip()
    category_id = request.POST.get('category_id', '')
    due_date = request.POST.get('due_date', '') or None

    if title:
        category = None
        if category_id:
            category = get_object_or_404(Category, id=category_id, member=request.user)
        Todo.objects.create(
            member=request.user, title=title, category=category, due_date=due_date
        )

    return render(request, 'partials/todos/todo_items.html', {**_context(request, category_id), 'show_oob': True})


@login_required
@require_POST
def todo_status_update(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id, member=request.user)
    status = request.POST.get('status', '')
    if status in Todo.Status.values:
        todo.status = status
        todo.save()
    return render(request, 'partials/todos/todo_card.html', {
        'todo': todo,
        'Status': Todo.Status,
        'categories': _member_categories(request.user),
    })


@login_required
@require_POST
def todo_category_update(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id, member=request.user)
    category_id = request.POST.get('category_id', '')
    todo.category = (
        get_object_or_404(Category, id=category_id, member=request.user)
        if category_id
        else None
    )
    todo.save()
    return render(request, 'partials/todos/todo_card.html', {
        'todo': todo,
        'Status': Todo.Status,
        'categories': _member_categories(request.user),
    })


@login_required
@require_POST
def todo_delete(request):
    category_id = request.POST.get('category_id', '')
    ids = [i for i in request.POST.get('ids', '').split(',') if i]
    Todo.objects.filter(member=request.user, id__in=ids).delete()
    return render(request, 'partials/todos/todo_items.html', {**_context(request, category_id), 'show_oob': True})


@login_required
@require_POST
def todo_due_date_update(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id, member=request.user)
    due_date = request.POST.get('due_date', '')
    todo.due_date = date.fromisoformat(due_date) if due_date else None
    todo.save()
    return render(request, 'partials/todos/todo_card.html', {
        'todo': todo,
        'Status': Todo.Status,
        'categories': _member_categories(request.user),
    })


@login_required
@require_POST
def category_create(request):
    name = request.POST.get('name', '').strip()
    if name:
        Category.objects.get_or_create(member=request.user, name=name)
    return redirect('todo_list')


def _category_list_context(member):
    return {
        'categories': _member_categories(member),
        'total_count': Todo.objects.filter(member=member).count(),
        'current_category_id': '',
    }


@login_required
@require_POST
def category_update(request, category_id):
    category = get_object_or_404(Category, id=category_id, member=request.user)
    name = request.POST.get('name', '').strip()
    if name:
        category.name = name
        try:
            category.save()
        except IntegrityError:
            pass
    return render(request, 'partials/todos/category_list.html', _category_list_context(request.user))


@login_required
@require_POST
def category_delete(request):
    ids = [i for i in request.POST.get('ids', '').split(',') if i]
    Category.objects.filter(member=request.user, id__in=ids).delete()
    return render(request, 'partials/todos/category_list.html', _category_list_context(request.user))
