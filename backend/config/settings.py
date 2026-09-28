import os
from pathlib import Path
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
SECRET_KEY = os.getenv("SECRET_KEY", "dev")
DEBUG = os.getenv("DEBUG", "0") == "1"
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = ["django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions",
    "django.contrib.messages", "corsheaders", "rest_framework", "accounts", "finance", "life"]
MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware", "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware"]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
TEMPLATES = []
DATABASES = {"default": {
       "ENGINE": "django.db.backends.mysql",
       "NAME": os.getenv("DB_NAME", "lifepulse"),
       "USER": os.getenv("DB_USER", "root"),
       "PASSWORD": os.getenv("DB_PASSWORD", ""),
       "HOST": os.getenv("DB_HOST", "localhost"),
       "PORT": os.getenv("DB_PORT", "3306"),
       "OPTIONS": {"charset": "utf8mb4"},
   }}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
TIME_ZONE = "Asia/Kolkata"; USE_TZ = True
CORS_ALLOW_ALL_ORIGINS = True
REST_FRAMEWORK = {"DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"]}
from datetime import timedelta
SIMPLE_JWT = {"ACCESS_TOKEN_LIFETIME": timedelta(hours=2), "REFRESH_TOKEN_LIFETIME": timedelta(days=14), "ROTATE_REFRESH_TOKENS": True}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com"); EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587")); EMAIL_TIMEOUT = 15; EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", ""); EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = f"LifePulse <{EMAIL_HOST_USER}>"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# ---- File storage for memory attachments: Oracle Object Storage when OCI_BUCKET is set, else the local media/ folder
MEDIA_ROOT = BASE_DIR / "media"; MEDIA_URL = "/media/"
_STATIC = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}
if os.getenv("OCI_BUCKET"):
    _region = os.getenv("OCI_REGION", "ap-hyderabad-1")
    os.environ.setdefault("AWS_REQUEST_CHECKSUM_CALCULATION", "when_required")   # newer boto3 versions add checksums Oracle's S3 API rejects
    os.environ.setdefault("AWS_RESPONSE_CHECKSUM_VALIDATION", "when_required")
    STORAGES = {"default": {"BACKEND": "storages.backends.s3.S3Storage", "OPTIONS": {
        "bucket_name": os.environ["OCI_BUCKET"], "endpoint_url": f"https://{os.environ['OCI_NAMESPACE']}.compat.objectstorage.{_region}.oraclecloud.com",
        "access_key": os.environ["OCI_ACCESS_KEY"], "secret_key": os.environ["OCI_SECRET_KEY"], "region_name": _region, "signature_version": "s3v4",
        "addressing_style": "path", "querystring_auth": True, "querystring_expire": 3600, "file_overwrite": False, "default_acl": None}}, "staticfiles": _STATIC}
else:
    STORAGES = {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}, "staticfiles": _STATIC}
