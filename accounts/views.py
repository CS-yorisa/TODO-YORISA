from django.contrib import auth
from django.contrib.auth import authenticate
from django.shortcuts import redirect, render


def signup(request):
    return render(request, "accounts/signup.html")


def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is None:
            return render(
                request,
                "accounts/login.html",
                {"error": "아이디 또는 비밀번호가 올바르지 않습니다."},
            )
        auth.login(request, user)
        return redirect("index")

    return render(request, "accounts/login.html")


def logout(request):
    auth.logout(request)
    return redirect("index")
