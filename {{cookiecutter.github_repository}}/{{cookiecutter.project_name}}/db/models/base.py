import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from crum import get_current_user

from ..mixins import AuditModel



class User(AbstractBaseUser):
    id = models.BigAutoField(unique=True, primary_key=True)

    username = models.CharField(max_length=128, unique=True)

    # user fields
    mobile_number = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)

    # tracking metrics
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Modified At")
    last_location = models.CharField(max_length=255, blank=True)
    created_location = models.CharField(max_length=255, blank=True)

    # the is' es
    is_superuser = models.BooleanField(default=False)
    is_managed = models.BooleanField(default=False)
    is_password_expired = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_password_autoset = models.BooleanField(default=False)

    token = models.CharField(max_length=64, blank=True)

    billing_address_country = models.CharField(max_length=255, default="INDIA")
    billing_address = models.JSONField(null=True)
    has_billing_address = models.BooleanField(default=False)

    user_timezone = models.CharField(max_length=255, default="Asia/Kolkata")

    last_active = models.DateTimeField(default=timezone.now, null=True)
    last_login_time = models.DateTimeField(null=True)
    last_logout_time = models.DateTimeField(null=True)
    last_login_ip = models.CharField(max_length=255, blank=True)
    last_logout_ip = models.CharField(max_length=255, blank=True)
    last_login_medium = models.CharField(
        max_length=20,
        default="email",
    )
    last_login_uagent = models.TextField(blank=True)
    token_updated_at = models.DateTimeField(null=True)

    USERNAME_FIELD = "username"
    # REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username

    class Meta:
        unique_together = [["mobile_number", "tenant"], ["email", "tenant"]]

    def save(self, *args, **kwargs):
        self.email = self.email.lower().strip()
        self.mobile_number = self.mobile_number.lower().strip()

        if self.token_updated_at is not None:
            self.token = uuid.uuid4().hex + uuid.uuid4().hex
            self.token_updated_at = timezone.now()

        if self.is_superuser:
            self.is_staff = True

        super(User, self).save(*args, **kwargs)


class BaseModel(AuditModel):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        user = get_current_user()

        if user is None or user.is_anonymous:
            self.created_by = None
            self.updated_by = None
            super(BaseModel, self).save(*args, **kwargs)
        else:
            self.created_by = user
            self.updated_by = user
            super(BaseModel, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.uuid)



def edison_welcome_mail(
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
        edison_welcome_mail(
            first_name,
            to_email,
            from_email,
            is_staff,
        )