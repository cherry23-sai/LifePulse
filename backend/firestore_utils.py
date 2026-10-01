from datetime import date, datetime
from firebase_db import db

def uid_of(user): return str(user.id)

def col(user, name):
    return db().collection("users").document(uid_of(user)).collection(name)

def clean(value):
    if isinstance(value, (datetime, date)): return value.isoformat()
    if isinstance(value, dict): return {k: clean(v) for k,v in value.items()}
    if isinstance(value, list): return [clean(v) for v in value]
    return value

def doc_data(doc):
    d=doc.to_dict() or {}; d["id"]=doc.id; return clean(d)
