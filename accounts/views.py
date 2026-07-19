from django.contrib import auth
from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from ninja import Router
from ninja.security import django_auth

from .models import Member
from .schemas import MemberOut, MemberSignupIn, MemberUpdateIn

router = Router(tags=["accounts"])


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


@router.post("/signup/", response={201: MemberOut, 400: dict})
def member_signup(request, payload: MemberSignupIn):
    if payload.password != payload.password_confirm:
        return 400, {"detail": "비밀번호가 일치하지 않습니다."}

    if Member.objects.filter(username=payload.username).exists():
        return 400, {"detail": "이미 사용 중인 아이디입니다."}
    if Member.objects.filter(email=payload.email).exists():
        return 400, {"detail": "이미 사용 중인 이메일입니다."}

    try:
        with transaction.atomic():
            member = Member.objects.create_user(
                username=payload.username,
                email=payload.email,
                password=payload.password,
                first_name=payload.first_name,
                last_name=payload.last_name,
            )
    except IntegrityError:
        return 400, {"detail": "이미 사용 중인 아이디 또는 이메일입니다."}

    return 201, member


@router.get("/me/", response=MemberOut, auth=django_auth)
def member_me(request):
    return request.user


@router.patch("/me/", response={200: MemberOut, 400: dict}, auth=django_auth)
def member_update(request, payload: MemberUpdateIn):
    data = payload.dict(exclude_unset=True)
    for attr, value in data.items():
        setattr(request.user, attr, value)

    try:
        with transaction.atomic():
            request.user.save()
    except IntegrityError:
        return 400, {"detail": "이미 사용 중인 이메일입니다."}

    return request.user


@router.delete("/me/", response={204: None}, auth=django_auth)
def member_withdraw(request):
    member = request.user
    member.is_active = False
    member.username = None
    member.email = None
    member.save()
    auth.logout(request)
    return 204, None
