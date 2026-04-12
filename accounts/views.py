from django.contrib import auth
from django.shortcuts import redirect, render

from .models import Member


def signup(request):
    if request.method == "POST":
        # TODO: 실제 회원가입 API 연동 시 교체
        return redirect("accounts:login")
    return render(request, "accounts/signup.html")


def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # TODO: 실제 로그인 API 연동 시 교체
        user, _ = Member.objects.get_or_create(
            username=username,
            defaults={"first_name": username},
        )
        auth.login(request, user)
        return redirect("index")

    return render(request, "accounts/login.html")


def logout(request):
    auth.logout(request)
    return redirect("index")
