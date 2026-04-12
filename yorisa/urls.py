"""
URL configuration for yorisa project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path

FEATURE_TEMPLATES = {
    "todo": "partials/feature_todo.html",
    "points": "partials/feature_points.html",
    "shop": "partials/feature_shop.html",
}


def index(request):
    return render(request, "index.html")


def feature_tab(request, tab):
    template = FEATURE_TEMPLATES.get(tab)
    if template is None:
        template = FEATURE_TEMPLATES["todo"]
    return render(request, template)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", index, name="index"),
    path("api/todos/", include("todos.urls")),
    path("features/<str:tab>/", feature_tab, name="feature_tab"),
]
