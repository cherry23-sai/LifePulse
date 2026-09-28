from django.conf import settings
from django.db import models
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    login_welcomed = models.BooleanField(default=False)


class EmailOTP(models.Model):
    PURPOSES = [("register", "register"), ("reset", "reset")]
    email = models.EmailField()
    purpose = models.CharField(max_length=10, choices=PURPOSES)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
