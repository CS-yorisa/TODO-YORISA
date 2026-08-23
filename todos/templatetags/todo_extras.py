from datetime import date

from django import template

register = template.Library()


@register.filter
def color_class(value):
    try:
        return f'cat-color-{int(value) % 8}'
    except (ValueError, TypeError):
        return 'cat-color-0'


@register.filter
def due_status(due_date):
    if not due_date:
        return 'none'
    today = date.today()
    if due_date < today:
        return 'overdue'
    elif due_date == today:
        return 'today'
    return 'upcoming'


@register.filter
def d_day_label(due_date):
    if not due_date:
        return ''
    delta = (due_date - date.today()).days
    if delta < 0:
        return ''
    if delta == 0:
        return 'D-DAY'
    return f'D-{delta}'
