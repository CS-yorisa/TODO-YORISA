from ninja import NinjaAPI
from django.urls import path

from accounts.api import router as auth_router
from todos.views import router
from . import views

api = NinjaAPI()
api.add_router("/todos/", router)
api.add_router("/auth/", auth_router)

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
