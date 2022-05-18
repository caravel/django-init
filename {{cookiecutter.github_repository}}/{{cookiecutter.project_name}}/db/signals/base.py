from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from {{ cookiecutter.project_name }}.db.models import User

def welcome_mail(
    first_name, to_email, from_email, is_staff
):
    subject = f"Welcome to {first_name}. Please verify your email"
    from_email_string = f"<{from_email}>"

    context = {
        "first_name": first_name,
    }

    if "@" in to_email:
        if is_staff:

            html_content = render_to_string("auth/admin_welcome_email.html", context)
            text_content = strip_tags(html_content)

            msg = EmailMultiAlternatives(
                subject, text_content, from_email_string, [to_email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        else:
            html_content = render_to_string("auth/user_welcome_email.html", context)
            text_content = strip_tags(html_content)
            email = EmailMultiAlternatives(
                subject, text_content, from_email_string, [to_email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
    return


@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    if created:
        first_name = instance.first_name.capitalize()
        to_email = instance.email
        from_email = "{{cookiecutter.project_name}} <{{cookiecutter.email}}>"
        is_staff = instance.is_staff
        welcome_mail(
            first_name,
            to_email,
            from_email,
            is_staff,
        )