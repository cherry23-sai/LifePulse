from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, LoginView, VerifyEmailView, ResendCodeView, ForgotPasswordView, ResetPasswordView

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("verify-email/", VerifyEmailView.as_view()),
    path("resend-code/", ResendCodeView.as_view()),
    path("login/", LoginView.as_view()),
    path("refresh/", TokenRefreshView.as_view()),
    path("forgot-password/", ForgotPasswordView.as_view()),
    path("reset-password/", ResetPasswordView.as_view()),
]
