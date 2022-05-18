from django.urls import path

# Create your urls here.

from {{cookiecutter.project_name}}.api.views.authentication import (
    SignInEndpoint,
    SignUpEndpoint,
    SignOutEndpoint,
)
from {{cookiecutter.project_name}}.api.views.people import (
    PeopleView
)

urlpatterns = [
    path("sign-in/", SignInEndpoint.as_view()),
    path("sign-up/", SignUpEndpoint.as_view()),
    path("sign-out/", SignOutEndpoint.as_view()),

    path("users/", PeopleView.as_view()),
]
