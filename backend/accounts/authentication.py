import jwt
from datetime import datetime, timezone
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from firebase_db import user_ref


ALGORITHM = "HS256"


class FirestoreUser:
    is_authenticated = True
    is_anonymous = False

    def __init__(self, data):
        self.id = data["id"]
        self.pk = data["id"]
        self.username = data.get("email", "")
        self.email = data.get("email", "")
        self.first_name = data.get("first_name", "")
        self.is_active = data.get("is_active", True)

    def __str__(self):
        return self.email


class FirestoreJWTAuthentication(BaseAuthentication):
    """
    JWT authentication for Firestore users.

    This intentionally does NOT inherit from SimpleJWT's JWTAuthentication,
    because SimpleJWT imports Django's ORM authentication/contenttypes models.
    LifePulse uses Firestore as its persistence layer.
    """

    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        if not header:
            return None

        parts = header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise AuthenticationFailed(
                "Invalid Authorization header. Use: Bearer <token>."
            )

        token = parts[1]

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[ALGORITHM],
                options={"require": ["exp", "iat", "user_id", "type"]},
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired.", code="token_expired")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token.", code="invalid_token")

        if payload.get("type") != "access":
            raise AuthenticationFailed("Access token required.", code="invalid_token")

        uid = payload.get("user_id")
        if not uid:
            raise AuthenticationFailed("Token has no user id.", code="user_not_found")

        doc = user_ref(uid).get()
        user = None
        if doc.exists:
            user = doc.to_dict()
            user["id"] = doc.id

        if not user or not user.get("is_active", False):
            raise AuthenticationFailed(
                "User not found or inactive.", code="user_not_found"
            )

        return FirestoreUser(user), payload
