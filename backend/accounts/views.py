import random, uuid
from datetime import timedelta
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjValidationError
from django.utils import timezone
from django.conf import settings
from rest_framework import serializers, permissions, views
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from . import emails
from firebase_db import db, user_ref

OTP_TTL = timedelta(minutes=10)
MAX_ATTEMPTS = 5

def _user_doc(email):
    q = db().collection("users").where("email", "==", email.lower()).limit(1).stream()
    return next(iter(q), None)

def get_user_by_email(email):
    d = _user_doc(email)
    if not d: return None
    x = d.to_dict(); x["id"] = d.id
    return x

def get_user_by_id(uid):
    d = user_ref(uid).get()
    if not d.exists: return None
    x = d.to_dict(); x["id"] = d.id
    return x

def _issue(email, purpose):
    col = db().collection("otps")
    for d in col.where("email", "==", email.lower()).where("purpose", "==", purpose).where("used", "==", False).stream():
        d.reference.update({"used": True})
    code = f"{random.randint(0, 999999):06d}"
    col.add({"email": email.lower(), "purpose": purpose, "code": code, "created_at": firestore_time(), "used": False, "attempts": 0})
    return code

def firestore_time():
    return timezone.now()

def _check(email, purpose, code):
    docs = list(db().collection("otps").where("email", "==", email.lower()).where("purpose", "==", purpose).where("used", "==", False).stream())
    if not docs: return None, "That code has expired. Request a new one."
    o = sorted(docs, key=lambda x: x.to_dict().get("created_at") or timezone.now(), reverse=True)[0]
    x = o.to_dict(); created = x.get("created_at")
    if created and timezone.now() - created > OTP_TTL:
        return None, "That code has expired. Request a new one."
    if x.get("attempts", 0) >= MAX_ATTEMPTS:
        return None, "Too many wrong attempts. Request a new code."
    if x.get("code") != str(code).strip():
        o.reference.update({"attempts": x.get("attempts", 0) + 1})
        return None, "Incorrect code."
    o.reference.update({"used": True})
    return o, None

def _tokens(user):
    # SimpleJWT is retained for the frontend token format, but no Django ORM user is used.
    # A lightweight object supplies the fields SimpleJWT needs.
    class U:
        def __init__(self, d):
            self.id = d["id"]; self.pk = d["id"]; self.username = d["email"]; self.email = d["email"]
            self.first_name = d.get("first_name",""); self.is_active = d.get("is_active", True)
            self.password = d.get("password","")
        def __str__(self): return self.username
    u = U(user)
    r = RefreshToken.for_user(u)
    return {"access": str(r.access_token), "refresh": str(r), "name": u.first_name}

class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=30)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    def validate_email(self, v):
        v=v.strip().lower()
        if get_user_by_email(v): raise serializers.ValidationError("Email already registered.")
        return v
    def validate_password(self,v):
        try: validate_password(v)
        except DjValidationError as e: raise serializers.ValidationError(e.messages)
        return v
    def validate_first_name(self,v):
        v=v.strip()
        if not v: raise serializers.ValidationError("Enter your name.")
        return v
    def create(self,d):
        from django.contrib.auth.hashers import make_password
        uid=uuid.uuid4().hex
        user={"email":d["email"],"first_name":d["first_name"],"password":make_password(d["password"]),
              "is_active":False,"login_welcomed":False,"created_at":firestore_time()}
        user_ref(uid).set(user)
        code=_issue(d["email"],"register"); emails.otp_verify(d["email"],d["first_name"],code)
        user["id"]=uid
        return user

class RegisterView(views.APIView):
    permission_classes=[permissions.AllowAny]
    def post(self,request):
        s=RegisterSerializer(data=request.data); s.is_valid(raise_exception=True); s.save()
        return Response({"detail":"We emailed you a 6-digit code. Enter it to verify your account."},201)

class VerifyEmailView(views.APIView):
    permission_classes=[permissions.AllowAny]
    def post(self,request):
        email=str(request.data.get("email","")).strip().lower(); code=request.data.get("code","")
        u=get_user_by_email(email)
        if not u:return Response({"detail":"No account with that email."},400)
        if u.get("is_active"):return Response({"detail":"This account is already verified. Sign in instead."},400)
        _,err=_check(email,"register",code)
        if err:return Response({"detail":err},400)
        user_ref(u["id"]).update({"is_active":True})
        u["is_active"]=True; emails.welcome(u)
        return Response(_tokens(u))

class ResendCodeView(views.APIView):
    permission_classes=[permissions.AllowAny]
    def post(self,request):
        email=str(request.data.get("email","")).strip().lower(); u=get_user_by_email(email)
        if u and not u.get("is_active"): emails.otp_verify(email,u.get("first_name",""),_issue(email,"register"))
        return Response({"detail":"If that email needs verifying, a new code is on its way."})

class ForgotPasswordView(views.APIView):
    permission_classes=[permissions.AllowAny]
    def post(self,request):
        email=str(request.data.get("email","")).strip().lower(); u=get_user_by_email(email)
        if u and u.get("is_active"): emails.otp_reset(email,u.get("first_name",""),_issue(email,"reset"))
        return Response({"detail":"If that email has an account, a reset code is on its way."})

class ResetPasswordView(views.APIView):
    permission_classes=[permissions.AllowAny]
    def post(self,request):
        email=str(request.data.get("email","")).strip().lower(); code=request.data.get("code",""); pw=request.data.get("password","")
        u=get_user_by_email(email)
        if not u:return Response({"detail":"No account with that email."},400)
        _,err=_check(email,"reset",code)
        if err:return Response({"detail":err},400)
        try: validate_password(pw)
        except DjValidationError as e:return Response({"detail":" ".join(e.messages)},400)
        from django.contrib.auth.hashers import make_password
        user_ref(u["id"]).update({"password":make_password(pw)})
        u["password"]=make_password(pw)
        return Response(_tokens(u))

class LoginView(views.APIView):
    permission_classes=[permissions.AllowAny]
    def post(self,request):
        email=str(request.data.get("username",request.data.get("email",""))).strip().lower()
        pw=request.data.get("password",""); u=get_user_by_email(email)
        from django.contrib.auth.hashers import check_password
        if not u or not u.get("is_active") or not check_password(pw,u.get("password","")):
            return Response({"detail":"No active account found with the supplied credentials."},401)
        if not u.get("login_welcomed"):
            emails.welcome_back(u); user_ref(u["id"]).update({"login_welcomed":True}); u["login_welcomed"]=True
        return Response(_tokens(u))
