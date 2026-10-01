import os
import json

import firebase_admin
from firebase_admin import credentials, firestore, storage

_app = None
_db = None
_bucket = None


def init_firebase():
    global _app, _db, _bucket

    if _app is not None:
        return _db

    # Render Secret File:
    # The file uploaded in Render is named:
    # firebase-service-account.json.json
    #
    # Render mounts Secret Files under /etc/secrets/
    secret_file_path = "/etc/secrets/firebase-service-account.json.json"

    # Allow an environment variable to override the default path.
    path = os.getenv("FIREBASE_SERVICE_ACCOUNT_FILE", "").strip()

    # If no path is configured, use the Render Secret File path.
    if not path:
        path = secret_file_path

    if os.path.exists(path):
        cred = credentials.Certificate(path)
    else:
        # Optional local-development fallback.
        local_path = os.path.join(
            os.path.dirname(__file__),
            "firebase-service-account.json.json",
        )

        if os.path.exists(local_path):
            cred = credentials.Certificate(local_path)
        else:
            # Also support raw JSON in an environment variable if needed.
            raw_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()

            if raw_json:
                try:
                    info = json.loads(raw_json)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(
                        "FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON."
                    ) from exc

                cred = credentials.Certificate(info)
            else:
                raise RuntimeError(
                    "Firebase service-account credentials were not found. "
                    "Expected Render Secret File at "
                    f"{secret_file_path}, or set "
                    "FIREBASE_SERVICE_ACCOUNT_FILE."
                )

    bucket_name = os.getenv(
        "FIREBASE_STORAGE_BUCKET",
        "lifepulse-37ad0.firebasestorage.app",
    ).strip()

    options = {}

    if bucket_name:
        options["storageBucket"] = bucket_name

    _app = firebase_admin.initialize_app(
        cred,
        options or None,
    )

    _db = firestore.client()

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
    """
    Accepts the FirestoreUser object used by DRF authentication,
    a user dictionary, or a raw user ID.
    """
    if hasattr(user, "id"):
        return str(user.id)

    if isinstance(user, dict):
        uid = user.get("id") or user.get("pk") or user.get("user_id")

        if uid:
            return str(uid)

    if user is not None:
        return str(user)

    raise ValueError("A valid user is required.")


def col(user, collection_name):
    """
    Return a Firestore subcollection belonging to the authenticated user.

    Example:
        col(request.user, "memories")

    resolves to:
        users/{user_id}/memories
    """
    name = str(collection_name).strip()

    if not name:
        raise ValueError("Firestore collection name cannot be empty.")

    return user_ref(_uid_from_user(user)).collection(name)


def now():
    return firestore.SERVER_TIMESTAMP


def ts_to_iso(v):
    if hasattr(v, "isoformat"):
        return v.isoformat()

    return v


def upload_file(file_obj, path, content_type=None):
    if _bucket is None:
        init_firebase()

    if _bucket is None:
        raise RuntimeError(
            "FIREBASE_STORAGE_BUCKET is not configured."
        )

    blob = _bucket.blob(path)

    blob.upload_from_file(
        file_obj,
        content_type=content_type or "application/octet-stream",
    )

    blob.make_public()

    return blob.public_url


def delete_file(path):
    if not path:
        return

    if _bucket is None:
        init_firebase()

    if _bucket is None:
        return

    try:
        _bucket.blob(path).delete()
    except Exception:
        # Deleting an already-missing attachment should not break the API.
        pass
