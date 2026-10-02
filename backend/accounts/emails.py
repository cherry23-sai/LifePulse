import logging
import threading
import base64
from email.message import EmailMessage
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.utils.html import escape

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from firebase_db import db

log = logging.getLogger(__name__)

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]


def _html(user, heading, lines, button):
    body = "".join(
        f'<p style="margin:0 0 12px">{escape(l)}</p>'
        for l in lines
    )

    return f"""
    <div style="
        font-family:Arial,sans-serif;
        max-width:520px;
        margin:auto;
        color:#171A3B;
    ">
        <h2 style="color:#4B4FE0">LifePulse</h2>

        <p>
            Hi {escape(user.get("first_name") or "there")},
        </p>

        <h3>{escape(heading)}</h3>

        {body}

        <p>
            <a href="{settings.FRONTEND_URL}">
                {escape(button)}
            </a>
        </p>
    </div>
    """


def _get_gmail_service():
    token_file = getattr(
        settings,
        "GMAIL_TOKEN_FILE",
        "/etc/secrets/gmail-token.json",
    )

    creds = Credentials.from_authorized_user_file(
        token_file,
        GMAIL_SCOPES,
    )

    if not creds or not creds.valid:
        raise RuntimeError(
            "Gmail OAuth credentials are missing or expired."
        )

    return build(
        "gmail",
        "v1",
        credentials=creds,
        cache_discovery=False,
    )


def send(
    user,
    subject,
    heading,
    lines,
    button="Open LifePulse",
    connection=None,
):
    try:
        sender = getattr(
            settings,
            "GMAIL_SENDER_EMAIL",
            "lifepulse.notify@gmail.com",
        )

        recipient = user["email"]

        text = (
            f"Hi {user.get('first_name') or 'there'},\n\n"
            + "\n\n".join(lines)
            + f"\n\n{button}: {settings.FRONTEND_URL}"
        )

        html = _html(
            user,
            heading,
            lines,
            button,
        )

        message = EmailMessage()

        message["To"] = recipient
        message["From"] = sender
        message["Subject"] = subject

        message.set_content(text)

        message.add_alternative(
            html,
            subtype="html",
        )

        encoded_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        service = _get_gmail_service()

        result = (
            service.users()
            .messages()
            .send(
                userId="me",
                body={
                    "raw": encoded_message
                },
            )
            .execute()
        )

        log.info(
            "LifePulse email sent to %s. Gmail message ID: %s",
            recipient,
            result.get("id"),
        )

        return True

    except Exception:
        log.exception(
            "Email to %s failed through Gmail API",
            user.get("email"),
        )

        return False


def _background(*args):
    threading.Thread(
        target=send,
        args=args,
        daemon=True,
    ).start()


def welcome(user):
    _background(
        user,
        "Welcome to LifePulse",
        "Your account is ready",
        [
            "Track your money, activities, habits and memories in one place.",
            "A good first step: add today's earnings, or plan tomorrow's to-do list tonight.",
        ],
    )


def welcome_back(user):
    _background(
        user,
        "Good to see you on LifePulse",
        "You're signed in",
        [
            "Start by adding today's earnings or tomorrow's plan.",
        ],
    )


def nightly_lines(user):
    uid = user["id"]
    d = str(timezone.localdate())

    acts = [
        x.to_dict()
        for x in (
            db()
            .collection("users")
            .document(uid)
            .collection("activities")
            .stream()
        )
        if x.to_dict().get("date") == d
    ]

    habits = [
        x.to_dict()
        for x in (
            db()
            .collection("users")
            .document(uid)
            .collection("habits")
            .stream()
        )
    ]

    logs = [
        x.to_dict()
        for x in (
            db()
            .collection("users")
            .document(uid)
            .collection("habit_logs")
            .stream()
        )
        if x.to_dict().get("date") == d
    ]

    todos = [
        x.to_dict()
        for x in (
            db()
            .collection("users")
            .document(uid)
            .collection("todos")
            .stream()
        )
        if x.to_dict().get("plan_date") == d
    ]

    lines = [
        (
            f"You have logged {len(acts)} activit"
            f"{'y' if len(acts) == 1 else 'ies'} today."
            if acts
            else
            "You have not logged today's activity yet. "
            "Add your phone hours, Rapido driving hours, study and exercise."
        )
    ]

    left = max(
        len(habits) - sum(
            1 for x in logs if x.get("done")
        ),
        0,
    )

    if left:
        lines.append(
            f"{left} habit"
            f"{' is' if left == 1 else 's are'} "
            "still not marked today."
        )

    review = sum(
        1
        for x in todos
        if not x.get("done")
        and not x.get("skip_reason")
    )

    if review:
        lines.append(
            f"{review} of today's to-dos still need a yes or no."
        )

    tomorrow = str(
        timezone.localdate()
        + timedelta(days=1)
    )

    if not any(
        x.to_dict().get("plan_date") == tomorrow
        for x in (
            db()
            .collection("users")
            .document(uid)
            .collection("todos")
            .stream()
        )
    ):
        lines.append(
            "Plan tomorrow's to-do list before you sleep."
        )

    return lines


def nightly(user, connection=None):
    return send(
        user,
        "Fill in today's activity on LifePulse",
        "Time to log your day",
        nightly_lines(user),
        "Log today's activity",
        connection,
    )


def otp_verify(email, name, code):
    return send(
        {
            "email": email,
            "first_name": name,
        },
        "Verify your email for LifePulse",
        "Confirm it's you",
        [
            f"Your verification code is {code}.",
            "It expires in 10 minutes.",
        ],
        "Open LifePulse",
    )


def otp_reset(email, name, code):
    return send(
        {
            "email": email,
            "first_name": name,
        },
        "Reset your LifePulse password",
        "Password reset code",
        [
            f"Your password reset code is {code}.",
            "It expires in 10 minutes.",
        ],
        "Open LifePulse",
    )