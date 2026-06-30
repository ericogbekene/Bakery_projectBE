# accounts/emails.py

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime


def _base_context(extra: dict = None) -> dict:
    """Shared context injected into every email template."""
    ctx = {
        "bakery_name": getattr(settings, "BAKERY_NAME", "M&C Cakes"),
        "frontend_url": getattr(settings, "FRONTEND_URL", "http://localhost:3000"),
        "year": datetime.now().year,
    }
    if extra:
        ctx.update(extra)
    return ctx


def send_html_email(subject: str, template_name: str, context: dict, recipient_email: str):
    """Core email sender — renders HTML template and sends via Brevo SMTP."""
    full_context = _base_context({"subject": subject, **context})
    html_content = render_to_string(template_name, full_context)

    plain_text = (
        f"{subject}\n\n"
        "Please open this email in an HTML-compatible client to view it properly.\n\n"
        f"Visit us at: {full_context['frontend_url']}"
    )

    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)


def send_verification_email(user, verification_token: str):
    """Sent immediately after registration."""
    verification_link = f"{settings.FRONTEND_URL}/verify-email/{verification_token}"
    send_html_email(
        subject="Verify your email address – action required",
        template_name="emails/verify_email.html",
        context={"user": user, "verification_link": verification_link},
        recipient_email=user.email,
    )


def send_welcome_email(user):
    """Sent after the user successfully verifies their email."""
    send_html_email(
        subject="Welcome to the family! Your account is ready 🎉",
        template_name="emails/welcome.html",
        context={"user": user},
        recipient_email=user.email,
    )


def send_password_reset_email(user, reset_link: str):
    """Sent when user requests a password reset."""
    send_html_email(
        subject="Reset your password",
        template_name="emails/password_reset.html",
        context={"user": user, "reset_link": reset_link},
        recipient_email=user.email,
    )


def send_password_reset_success_email(user):
    """Sent after a successful password reset."""
    send_html_email(
        subject="Your password has been changed",
        template_name="emails/password_reset_success.html",
        context={"user": user},
        recipient_email=user.email,
    )