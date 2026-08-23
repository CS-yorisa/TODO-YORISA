from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("password/find/", views.password_find, name="password_find"),
    path("mypage/", views.mypage, name="mypage"),
    path("mypage/verify/", views.mypage_verify, name="mypage_verify"),
    path("mypage/edit/", views.mypage_edit, name="mypage_edit"),
    path("mypage/password/verify/", views.password_verify, name="password_verify"),
    path("mypage/password/edit/", views.password_edit, name="password_edit"),
]
