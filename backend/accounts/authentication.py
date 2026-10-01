from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .views import get_user_by_id

class FirestoreUser:
    is_authenticated = True
    is_anonymous = False
    def __init__(self, data):
        self.id=data["id"]; self.pk=data["id"]; self.username=data.get("email","")
        self.email=data.get("email",""); self.first_name=data.get("first_name","")
        self.is_active=data.get("is_active",True)
    def __str__(self): return self.email

class FirestoreJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        uid = validated_token.get("user_id")
        if not uid: raise AuthenticationFailed("Token has no user id.", code="user_not_found")
        user=get_user_by_id(uid)
        if not user or not user.get("is_active"): raise AuthenticationFailed("User not found.", code="user_not_found")
        return FirestoreUser(user)
