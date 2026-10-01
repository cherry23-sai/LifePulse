from django.core.mail import get_connection
from django.core.management.base import BaseCommand,CommandError
from accounts.emails import nightly,nightly_lines
from firebase_db import db
class Command(BaseCommand):
    help="Email every active Firestore user the 9 PM activity reminder."
    def add_arguments(self,p):
        p.add_argument("--to");p.add_argument("--dry-run",action="store_true")
    def handle(self,*a,**o):
        users=[]
        for d in db().collection("users").where("is_active","==",True).stream():
            u=d.to_dict();u["id"]=d.id
            if u.get("email") and (not o["to"] or u["email"].lower()==o["to"].lower()):users.append(u)
        ok=fail=0
        with get_connection() as conn:
            for u in users:
                if o["dry_run"]:self.stdout.write(f"{u['email']}: "+" | ".join(nightly_lines(u)))
                elif nightly(u,conn):ok+=1
                else:fail+=1
        if not o["dry_run"]:self.stdout.write(f"Sent {ok}, failed {fail}")
        if fail:raise CommandError(f"{fail} email(s) failed.")
