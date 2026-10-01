from django.urls import path

from .views import (
    RegisterView,
    LoginView,
    VerifyEmailView,
    ResendCodeView,
    ForgotPasswordView,
    ResetPasswordView,
    RefreshView,
)


urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("verify-email/", VerifyEmailView.as_view()),
    path("resend-code/", ResendCodeView.as_view()),
    path("login/", LoginView.as_view()),
    path("refresh/", RefreshView.as_view()),
    path("forgot-password/", ForgotPasswordView.as_view()),
    path("reset-password/", ResetPasswordView.as_view()),
]
