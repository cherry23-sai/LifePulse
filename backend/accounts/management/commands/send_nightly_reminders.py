from django.contrib.auth.models import User
from django.core.mail import get_connection
from django.core.management.base import BaseCommand, CommandError
from accounts.emails import nightly, nightly_lines

class Command(BaseCommand):
    help = "Email every active user the 9 PM activity reminder. Schedule it with cron (see README)."
    def add_arguments(self, p):
        p.add_argument("--to", help="send only to this registered email address (use it to test your mail settings)")
        p.add_argument("--dry-run", action="store_true", help="list recipients and the message lines without sending")
    def handle(self, *a, **o):
        users = User.objects.filter(is_active=True).exclude(email="")
        if o["to"]: users = users.filter(email__iexact=o["to"])
        ok = fail = 0
        with get_connection() as conn:   # one mail-server connection for the whole run
            for u in users:
                if o["dry_run"]: self.stdout.write(f"{u.email}: " + " | ".join(nightly_lines(u))); continue
                if nightly(u, conn): ok += 1
                else: fail += 1
        if not o["dry_run"]: self.stdout.write(f"Sent {ok}, failed {fail}")
        if fail: raise CommandError(f"{fail} email(s) failed. Check EMAIL_* settings; details are in the log above.")
