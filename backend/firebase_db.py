import os, json, base64
import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud.firestore_v1.base_query import FieldFilter

_app = None
_db = None
_bucket = None

def init_firebase():
    global _app, _db, _bucket
    if _app is not None:
        return _db
    raw_b64 = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON_BASE64", "backend\\firebase-service-account.json.json").strip()
    raw_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    path = os.getenv("FIREBASE_SERVICE_ACCOUNT_FILE", "").strip()
    if raw_b64:
        info = json.loads(base64.b64decode(raw_b64).decode("utf-8"))
        cred = credentials.Certificate(info)
    elif raw_json:
        cred = credentials.Certificate(json.loads(raw_json))
    elif path:
        cred = credentials.Certificate(path)
    else:
        raise RuntimeError("Firebase credentials are not configured. Set FIREBASE_SERVICE_ACCOUNT_JSON_BASE64, FIREBASE_SERVICE_ACCOUNT_JSON, or FIREBASE_SERVICE_ACCOUNT_FILE.")
    options = {}
    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET", "lifepulse-37ad0.firebasestorage.app").strip()
    if bucket_name:
        options["storageBucket"] = bucket_name
    _app = firebase_admin.initialize_app(cred, options or None)
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

def now():
    return firestore.SERVER_TIMESTAMP

def ts_to_iso(v):
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return v

def upload_file(file_obj, path, content_type=None):
    if _bucket is None:
        raise RuntimeError("FIREBASE_STORAGE_BUCKET is not configured.")
    blob = _bucket.blob(path)
    blob.upload_from_file(file_obj, content_type=content_type or "application/octet-stream")
    blob.make_public()
    return blob.public_url

def delete_file(path):
    if _bucket is None:
        return
    try:
        _bucket.blob(path).delete()
    except Exception:
        pass
