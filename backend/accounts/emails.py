import logging, threading
from datetime import timedelta
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.utils.html import escape
log = logging.getLogger(__name__)

def _html(user, heading, lines, button):
    body = "".join(f'<p style="margin:0 0 12px">{escape(l)}</p>' for l in lines)
    return (f'<div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;color:#171A3B"><h2 style="color:#4B4FE0;margin:0 0 16px">LifePulse</h2>'
            f'<p>Hi {escape(user.first_name or "there")},</p><h3>{escape(heading)}</h3>{body}<p><a href="{settings.FRONTEND_URL}" style="background:#4B4FE0;color:#fff;'
            f'padding:10px 18px;border-radius:8px;text-decoration:none;display:inline-block">{escape(button)}</a></p>'
            '<p style="color:#5F6488;font-size:12px">You are receiving this because you have a LifePulse account.</p></div>')

def send(user, subject, heading, lines, button="Open LifePulse", connection=None):
    """Send one HTML + plain-text email. Returns False (and logs the reason) instead of raising."""
    text = f"Hi {user.first_name or 'there'},\n\n" + "\n\n".join(lines) + f"\n\n{button}: {settings.FRONTEND_URL}"
    try:
        m = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, [user.email], connection=connection)
        m.attach_alternative(_html(user, heading, lines, button), "text/html"); m.send(); return True
    except Exception:
        log.exception("Email to %s failed", user.email); return False

def _background(*args):  # keeps sign-up and login fast even when the mail server is slow
    threading.Thread(target=send, args=args, daemon=True).start()

def welcome(user):
    _background(user, "Welcome to LifePulse", "Your account is ready", ["Track your money, activities, habits and memories in one place.",
                "A good first step: add today's earnings, or plan tomorrow's to-do list tonight."])
def welcome_back(user):
    _background(user, "Good to see you on LifePulse", "You're signed in", ["Start by adding today's earnings or tomorrow's plan."])

def nightly_lines(user):
    from life.models import Todo, Activity   # imported here so accounts does not depend on life at start-up
    from life.views import habit_rows
    d = timezone.localdate(); n = Activity.objects.filter(user=user, date=d).count()
    lines = [f"You have logged {n} activit{'y' if n == 1 else 'ies'} today. Add anything you missed, such as phone hours, Rapido driving, study or exercise." if n
             else "You have not logged today's activity yet. Add your phone hours, Rapido driving hours, study and exercise."]
    left = sum(1 for r in habit_rows(user, d) if r["done"] is None)
    if left: lines.append(f"{left} habit{'s are' if left != 1 else ' is'} still not marked today.")
    review = Todo.objects.filter(user=user, plan_date=d, done=False, skip_reason="").count()
    if review: lines.append(f"{review} of today's to-dos still need a yes or no.")
    if not Todo.objects.filter(user=user, plan_date=d + timedelta(days=1)).exists(): lines.append("Plan tomorrow's to-do list before you sleep.")
    return lines

def nightly(user, connection=None):
    return send(user, "Fill in today's activity on LifePulse", "Time to log your day", nightly_lines(user), "Log today's activity", connection)

class _Addressee:
    def __init__(self, email, name): self.email, self.first_name = email, name

def otp_verify(email, name, code):
    return send(_Addressee(email, name), "Verify your email for LifePulse", "Confirm it's you",
                [f"Your verification code is {code}.", "It expires in 10 minutes. Enter it on the LifePulse sign-up screen."], "Open LifePulse")

def otp_reset(email, name, code):
    return send(_Addressee(email, name), "Reset your LifePulse password", "Password reset code",
                [f"Your reset code is {code}.", "It expires in 10 minutes. If you did not ask for this, you can ignore this email."], "Open LifePulse")
