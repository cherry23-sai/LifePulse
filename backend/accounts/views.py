import random
import uuid
import jwt

from datetime import timedelta, datetime, timezone

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjValidationError
from django.utils import timezone as django_timezone
from django.conf import settings

from rest_framework import serializers, permissions, views
from rest_framework.response import Response

from . import emails
from firebase_db import db, user_ref


OTP_TTL = timedelta(minutes=10)
MAX_ATTEMPTS = 5
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TTL = timedelta(hours=2)
REFRESH_TOKEN_TTL = timedelta(days=14)


def _user_doc(email):
    q = (
        db()
        .collection("users")
        .where("email", "==", email.lower())
        .limit(1)
        .stream()
    )
    return next(iter(q), None)


def get_user_by_email(email):
    d = _user_doc(email)
    if not d:
        return None
    x = d.to_dict()
    x["id"] = d.id
    return x


def get_user_by_id(uid):
    if not uid:
        return None
    d = user_ref(uid).get()
    if not d.exists:
        return None
    x = d.to_dict()
    x["id"] = d.id
    return x


def _issue(email, purpose):
    col = db().collection("otps")

    for d in (
        col.where("email", "==", email.lower())
        .where("purpose", "==", purpose)
        .where("used", "==", False)
        .stream()
    ):
        d.reference.update({"used": True})

    code = f"{random.randint(0, 999999):06d}"
    col.add(
        {
            "email": email.lower(),
            "purpose": purpose,
            "code": code,
            "created_at": firestore_time(),
            "used": False,
            "attempts": 0,
        }
    )
    return code


def firestore_time():
    return django_timezone.now()


def _check(email, purpose, code):
    docs = list(
        db()
        .collection("otps")
        .where("email", "==", email.lower())
        .where("purpose", "==", purpose)
        .where("used", "==", False)
        .stream()
    )

    if not docs:
        return None, "That code has expired. Request a new one."

    o = sorted(
        docs,
        key=lambda x: x.to_dict().get("created_at") or django_timezone.now(),
        reverse=True,
    )[0]

    x = o.to_dict()
    created = x.get("created_at")

    if created and django_timezone.now() - created > OTP_TTL:
        return None, "That code has expired. Request a new one."

    if x.get("attempts", 0) >= MAX_ATTEMPTS:
        return None, "Too many wrong attempts. Request a new code."

    if x.get("code") != str(code).strip():
        o.reference.update({"attempts": x.get("attempts", 0) + 1})
        return None, "Incorrect code."

    o.reference.update({"used": True})
    return o, None


def _make_token(user, token_type, lifetime):
    now = datetime.now(timezone.utc)

    payload = {
        "user_id": user["id"],
        "email": user.get("email", ""),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()),
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def _tokens(user):
    return {
        "access": _make_token(user, "access", ACCESS_TOKEN_TTL),
        "refresh": _make_token(user, "refresh", REFRESH_TOKEN_TTL),
        "name": user.get("first_name", ""),
    }


class RefreshView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh = str(request.data.get("refresh", "")).strip()

        if not refresh:
            return Response({"detail": "Refresh token is required."}, 400)

        try:
            payload = jwt.decode(
                refresh,
                settings.SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
                options={"require": ["exp", "iat", "user_id", "type"]},
            )
        except jwt.ExpiredSignatureError:
            return Response({"detail": "Refresh token has expired."}, 401)
        except jwt.InvalidTokenError:
            return Response({"detail": "Invalid refresh token."}, 401)

        if payload.get("type") != "refresh":
            return Response({"detail": "Refresh token required."}, 401)

        user = get_user_by_id(payload.get("user_id"))

        if not user or not user.get("is_active", False):
            return Response({"detail": "User not found or inactive."}, 401)

        return Response(
            {
                "access": _make_token(user, "access", ACCESS_TOKEN_TTL),
                "refresh": refresh,
                "name": user.get("first_name", ""),
            }
        )


class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=30)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, v):
        v = v.strip().lower()
        if get_user_by_email(v):
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
        return v

    def create(self, d):
        from django.contrib.auth.hashers import make_password

        uid = uuid.uuid4().hex
        user = {
            "email": d["email"],
            "first_name": d["first_name"],
            "password": make_password(d["password"]),
            "is_active": False,
            "login_welcomed": False,
            "created_at": firestore_time(),
        }

        user_ref(uid).set(user)

        code = _issue(d["email"], "register")
        emails.otp_verify(d["email"], d["first_name"], code)

        user["id"] = uid
        return user


class RegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()

        return Response(
            {
                "detail": "We emailed you a 6-digit code. Enter it to verify your account."
            },
            201,
        )


class VerifyEmailView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        code = request.data.get("code", "")

        u = get_user_by_email(email)

        if not u:
            return Response({"detail": "No account with that email."}, 400)

        if u.get("is_active"):
            return Response(
                {"detail": "This account is already verified. Sign in instead."},
                400,
            )

        _, err = _check(email, "register", code)

        if err:
            return Response({"detail": err}, 400)

        user_ref(u["id"]).update({"is_active": True})
        u["is_active"] = True

        emails.welcome(u)

        return Response(_tokens(u))


class ResendCodeView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        u = get_user_by_email(email)

        if u and not u.get("is_active"):
            emails.otp_verify(
                email,
                u.get("first_name", ""),
                _issue(email, "register"),
            )

        return Response(
            {
                "detail": "If that email needs verifying, a new code is on its way."
            }
        )


class ForgotPasswordView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        u = get_user_by_email(email)

        if u and u.get("is_active"):
            emails.otp_reset(
                email,
                u.get("first_name", ""),
                _issue(email, "reset"),
            )

        return Response(
            {
                "detail": "If that email has an account, a reset code is on its way."
            }
        )


class ResetPasswordView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        code = request.data.get("code", "")
        pw = request.data.get("password", "")

        u = get_user_by_email(email)

        if not u:
            return Response({"detail": "No account with that email."}, 400)

        _, err = _check(email, "reset", code)

        if err:
            return Response({"detail": err}, 400)

        try:
            validate_password(pw)
        except DjValidationError as e:
            return Response({"detail": " ".join(e.messages)}, 400)

        from django.contrib.auth.hashers import make_password

        hashed = make_password(pw)
        user_ref(u["id"]).update({"password": hashed})
        u["password"] = hashed

        return Response(_tokens(u))


class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = str(
            request.data.get("username", request.data.get("email", ""))
        ).strip().lower()
        pw = request.data.get("password", "")

        u = get_user_by_email(email)

        from django.contrib.auth.hashers import check_password

        if (
            not u
            or not u.get("is_active")
            or not check_password(pw, u.get("password", ""))
        ):
            return Response(
                {"detail": "No active account found with the supplied credentials."},
                401,
            )

        if not u.get("login_welcomed"):
            emails.welcome_back(u)
            user_ref(u["id"]).update({"login_welcomed": True})
            u["login_welcomed"] = True

        return Response(_tokens(u))
