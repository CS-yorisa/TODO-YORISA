from django.urls import path

from . import views

urlpatterns = [
    path('', views.todo_list, name='todo_list'),
    path('create/', views.todo_create, name='todo_create'),
    path('<int:todo_id>/status/', views.todo_status_update, name='todo_status_update'),
    path('<int:todo_id>/category/', views.todo_category_update, name='todo_category_update'),
    path('<int:todo_id>/due-date/', views.todo_due_date_update, name='todo_due_date_update'),
    path('delete/', views.todo_delete, name='todo_delete'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:category_id>/update/', views.category_update, name='category_update'),
    path('categories/delete/', views.category_delete, name='category_delete'),
]
