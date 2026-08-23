from django.contrib import auth
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

# TODO: 실제 회원 정보 조회/수정 API가 붙기 전까지 사용하는 목(mock) 데이터.
# API 연동 담당자가 작업 완료하면 이 값 대신 API 응답으로 교체 예정.
MOCK_PROFILE = {
    "username": "mock_user",
    "last_name": "홍",
    "first_name": "길동",
    "email": "mock@example.com",
}


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
        return redirect("todo_list")

    return render(request, "accounts/login.html")


def logout(request):
    auth.logout(request)
    return redirect("index")


def password_find(request):
    # TODO: 실제 비밀번호 찾기(본인 확인 후 재설정 메일 발송 등) 로직 연동 (다른 담당자 작업). 지금은 화면만 확인.
    sent = request.method == "POST"
    return render(request, "accounts/password_find.html", {"sent": sent})


@login_required
def mypage(request):
    # TODO: 실제 회원 정보 조회 API 연동 (다른 담당자 작업). 지금은 MOCK_PROFILE 표시.
    return render(request, "accounts/mypage.html", {"profile": MOCK_PROFILE})


@login_required
def mypage_verify(request):
    # TODO: 실제 비밀번호 재확인 로직 연동 (다른 담당자 작업). 지금은 입력만 받고 통과시킴.
    if request.method == "POST":
        return redirect("accounts:mypage_edit")
    return render(request, "accounts/mypage_verify.html")


@login_required
def mypage_edit(request):
    # TODO: 실제 회원 정보 수정 API 연동 (다른 담당자 작업). 지금은 저장하지 않고 화면만 확인.
    if request.method == "POST":
        return redirect("accounts:mypage")
    return render(request, "accounts/mypage_edit.html", {"profile": MOCK_PROFILE})


@login_required
def password_verify(request):
    # TODO: 실제 비밀번호 재확인 로직 연동 (다른 담당자 작업). 지금은 입력만 받고 통과시킴.
    if request.method == "POST":
        return redirect("accounts:password_edit")
    return render(request, "accounts/password_verify.html")


@login_required
def password_edit(request):
    # TODO: 실제 비밀번호 변경 API 연동 (다른 담당자 작업). 지금은 저장하지 않고 화면만 확인.
    if request.method == "POST":
        return redirect("accounts:mypage")
    return render(request, "accounts/password_edit.html")
