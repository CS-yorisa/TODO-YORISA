from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Case, Count, IntegerField, Value, When
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from todos.models import Category, Todo


def _member_categories(member):
    return Category.objects.filter(member=member).annotate(todo_count=Count('todos'))


def _due_soon_count(member):
    today = date.today()
    return Todo.objects.filter(
        member=member, due_date__gte=today, due_date__lte=today + timedelta(days=6)
    ).exclude(status=Todo.Status.DONE).count()


def _context(request, category_id='', status_filter='', due_filter=''):
    todos = Todo.objects.filter(member=request.user)
    if category_id:
        todos = todos.filter(category_id=category_id)
    if status_filter:
        todos = todos.filter(status=status_filter)
    if due_filter == 'week':
        today = date.today()
        todos = todos.filter(
            due_date__gte=today, due_date__lte=today + timedelta(days=6)
        ).exclude(status=Todo.Status.DONE)
    today = date.today()
    todos = todos.annotate(
        is_overdue=Case(
            When(
                due_date__lt=today,
                status__in=[Todo.Status.TODO, Todo.Status.IN_PROGRESS],
                then=Value(1),
            ),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by('-is_overdue', 'id')
    return {
        'todos': todos,
        'categories': _member_categories(request.user),
        'total_count': Todo.objects.filter(member=request.user).count(),
        'status_filter': status_filter,
        'current_category_id': category_id,
        'due_filter': due_filter,
        'due_soon_count': _due_soon_count(request.user),
        'Status': Todo.Status,
    }


@login_required
def todo_list(request):
    category_id = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    due_filter = request.GET.get('due', '')
    ctx = _context(request, category_id, status_filter, due_filter)
    hx_target = request.headers.get('HX-Target', '')
    if hx_target == 'todo-list':
        return render(request, 'todos/components/todo_items.html', ctx)
    elif request.headers.get('HX-Request'):
        return render(request, 'todos/components/todo_section.html', ctx)
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

    return render(request, 'todos/components/todo_items.html', {**_context(request, category_id), 'show_oob': True})


@login_required
@require_POST
def todo_status_update(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id, member=request.user)
    status = request.POST.get('status', '')
    if status in Todo.Status.values:
        todo.status = status
        todo.save()
    return render(request, 'todos/components/todo_card.html', {
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
    return render(request, 'todos/components/todo_card.html', {
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
    return render(request, 'todos/components/todo_items.html', {**_context(request, category_id), 'show_oob': True})


@login_required
@require_POST
def todo_due_date_update(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id, member=request.user)
    due_date = request.POST.get('due_date', '')
    todo.due_date = date.fromisoformat(due_date) if due_date else None
    todo.save()
    return render(request, 'todos/components/todo_card.html', {
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
    return render(request, 'todos/components/category_list.html', _category_list_context(request.user))


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
    return render(request, 'todos/components/category_list.html', _category_list_context(request.user))


@login_required
@require_POST
def category_delete(request):
    ids = [i for i in request.POST.get('ids', '').split(',') if i]
    Category.objects.filter(member=request.user, id__in=ids).delete()
    return render(request, 'todos/components/category_list.html', _category_list_context(request.user))
