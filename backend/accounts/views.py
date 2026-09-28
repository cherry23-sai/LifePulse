import random
from datetime import timedelta
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjValidationError
from django.utils import timezone
from rest_framework import serializers, generics, permissions, views
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Profile, EmailOTP
from . import emails

OTP_TTL = timedelta(minutes=10)
MAX_ATTEMPTS = 5


def _issue(email, purpose):
    EmailOTP.objects.filter(email__iexact=email, purpose=purpose, used=False).update(used=True)  # invalidate older codes
    code = f"{random.randint(0, 999999):06d}"
    EmailOTP.objects.create(email=email.lower(), purpose=purpose, code=code)
    return code


def _check(email, purpose, code):
    o = EmailOTP.objects.filter(email__iexact=email, purpose=purpose, used=False).order_by("-created_at").first()
    if not o or timezone.now() - o.created_at > OTP_TTL:
        return None, "That code has expired. Request a new one."
    if o.attempts >= MAX_ATTEMPTS:
        return None, "Too many wrong attempts. Request a new code."
    if o.code != str(code).strip():
        o.attempts += 1; o.save(update_fields=["attempts"])
        return None, "Incorrect code."
    o.used = True; o.save(update_fields=["used"])
    return o, None


def _tokens(user):
    r = RefreshToken.for_user(user)
    return {"access": str(r.access_token), "refresh": str(r), "name": user.first_name}


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}, "first_name": {"required": True}}

    def validate_email(self, v):
        v = v.strip().lower()
        if User.objects.filter(username__iexact=v).exists():
            raise serializers.ValidationError("Email already registered.")
        return v

    def validate_password(self, v):
        try:
            validate_password(v)
        except DjValidationError as e:
            raise serializers.ValidationError(e.messages)
        return v

    def validate_first_name(self, v):
        v = v.strip()
        if not v:
            raise serializers.ValidationError("Enter your name.")
        return v[:30]

    def create(self, d):
        u = User.objects.create_user(username=d["email"], email=d["email"], password=d["password"], first_name=d["first_name"], is_active=False)
        Profile.objects.create(user=u)
        emails.otp_verify(u.email, u.first_name, _issue(u.email, "register"))
        return u


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *a, **kw):
        r = super().create(request, *a, **kw)
        return Response({"detail": "We emailed you a 6-digit code. Enter it to verify your account."}, 201)


class VerifyEmailView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email, code = str(request.data.get("email", "")).strip().lower(), request.data.get("code", "")
        u = User.objects.filter(username__iexact=email).first()
        if not u:
            return Response({"detail": "No account with that email."}, 400)
        if u.is_active:
            return Response({"detail": "This account is already verified. Sign in instead."}, 400)
        _, err = _check(email, "register", code)
        if err:
            return Response({"detail": err}, 400)
        u.is_active = True; u.save(update_fields=["is_active"])
        emails.welcome(u)
        return Response(_tokens(u))


class ResendCodeView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        u = User.objects.filter(username__iexact=email, is_active=False).first()
        if u:
            emails.otp_verify(u.email, u.first_name, _issue(email, "register"))
        return Response({"detail": "If that email needs verifying, a new code is on its way."})


class ForgotPasswordView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        u = User.objects.filter(username__iexact=email, is_active=True).first()
        if u:
            emails.otp_reset(u.email, u.first_name, _issue(email, "reset"))
        return Response({"detail": "If that email has an account, a reset code is on its way."})


class ResetPasswordView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email, code, pw = str(request.data.get("email", "")).strip().lower(), request.data.get("code", ""), request.data.get("password", "")
        u = User.objects.filter(username__iexact=email, is_active=True).first()
        if not u:
            return Response({"detail": "No account with that email."}, 400)
        _, err = _check(email, "reset", code)
        if err:
            return Response({"detail": err}, 400)
        try:
            validate_password(pw, u)
        except DjValidationError as e:
            return Response({"detail": " ".join(e.messages)}, 400)
        u.set_password(pw); u.save()
        return Response(_tokens(u))


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get("username", "").strip().lower(); attrs["username"] = email
        if User.objects.filter(username__iexact=email, is_active=False).exists():
            raise serializers.ValidationError({"detail": "Verify your email first. Check your inbox for the code, or ask us to resend it."})
        data = super().validate(attrs)
        p, _ = Profile.objects.get_or_create(user=self.user)
        if not p.login_welcomed:
            emails.welcome_back(self.user); p.login_welcomed = True; p.save()
        data["name"] = self.user.first_name
        return data


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
