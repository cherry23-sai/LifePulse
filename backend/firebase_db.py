import os
import json
import base64

import firebase_admin
from firebase_admin import credentials, firestore, storage

_app = None
_db = None
_bucket = None


def init_firebase():
    global _app, _db, _bucket

    if _app is not None:
        return _db

    # Render Secret File
    path = os.getenv("FIREBASE_SERVICE_ACCOUNT_FILE", "").strip()

    # Optional JSON / Base64 environment variables
    raw_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    raw_b64 = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON_BASE64", "").strip()

    # 1. Prefer the Render Secret File
    if path:
        if not os.path.exists(path):
            raise RuntimeError(
                f"Firebase service-account file was not found: {path}"
            )

        cred = credentials.Certificate(path)

    # 2. Optional raw JSON environment variable
    elif raw_json:
        try:
            info = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON."
            ) from exc

        cred = credentials.Certificate(info)

    # 3. Optional Base64 environment variable
    elif raw_b64:
        try:
            info = json.loads(
                base64.b64decode(raw_b64).decode("utf-8")
            )
        except Exception as exc:
            raise RuntimeError(
                "FIREBASE_SERVICE_ACCOUNT_JSON_BASE64 "
                "is not valid Base64-encoded JSON."
            ) from exc

        cred = credentials.Certificate(info)

    # 4. Local development fallback
    else:
        local_path = os.path.join(
            os.path.dirname(__file__),
            "firebase-service-account.json.json"
        )

        if os.path.exists(local_path):
            cred = credentials.Certificate(local_path)
        else:
            raise RuntimeError(
                "Firebase credentials are not configured. "
                "Set FIREBASE_SERVICE_ACCOUNT_FILE, "
                "FIREBASE_SERVICE_ACCOUNT_JSON, or "
                "FIREBASE_SERVICE_ACCOUNT_JSON_BASE64."
            )

    bucket_name = os.getenv(
        "FIREBASE_STORAGE_BUCKET",
        "lifepulse-37ad0.firebasestorage.app"
    ).strip()

    options = {}

    if bucket_name:
        options["storageBucket"] = bucket_name

    _app = firebase_admin.initialize_app(
        cred,
        options or None
    )

    _db = firestore.client(database_id="default")

    if bucket_name:
        _bucket = storage.bucket(app=_app)

    return _db


def db():
    return init_firebase()


def users():
    return db().collection("users")


def user_ref(uid):
    return users().document(str(uid))


def _uid_from_user(user):
    if hasattr(user, "id"):
        return str(user.id)

    if isinstance(user, dict):
        uid = (
            user.get("id")
            or user.get("pk")
            or user.get("user_id")
        )

        if uid:
            return str(uid)

    if user is not None:
        return str(user)

    raise ValueError("A valid user is required.")


def col(user, collection_name):
    name = str(collection_name).strip()

    if not name:
        raise ValueError(
            "Firestore collection name cannot be empty."
        )

    return user_ref(
        _uid_from_user(user)
    ).collection(name)


def now():
    return firestore.SERVER_TIMESTAMP


def ts_to_iso(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()

    return value


def upload_file(file_obj, path, content_type=None):
    global _bucket

    if _bucket is None:
        init_firebase()

    if _bucket is None:
        raise RuntimeError(
            "FIREBASE_STORAGE_BUCKET is not configured."
        )

    blob = _bucket.blob(path)

    blob.upload_from_file(
        file_obj,
        content_type=(
            content_type
            or "application/octet-stream"
        )
    )

    blob.make_public()

    return blob.public_url


def delete_file(path):
    global _bucket

    if not path:
        return

    if _bucket is None:
        init_firebase()

    if _bucket is None:
        return

    try:
        _bucket.blob(path).delete()
    except Exception:
        pass