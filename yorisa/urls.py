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

from yorisa.api import api


def index(request):
    return render(request, "index.html")


urlpatterns = [
    # 서비스 진입점
    path("", index, name="index"),
    # 관리자
    path("admin/", admin.site.urls),
    # REST API (django-ninja) — 라우터 마운트는 yorisa/api.py 참고
    path("api/", api.urls),
    # 앱 템플릿 뷰
    path("accounts/", include("accounts.urls")),
    path("todos/", include("todos.urls")),
]
