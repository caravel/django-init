# accounts.utils
import uuid
import re

# accounts.views

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from sentry_sdk import capture_exception, capture_message

from {{ cookiecutter.project_name }}.db.models import User
from {{ cookiecutter.project_name }}.api.serializers.people import UserSerializer




PHONE_NUMBER_REGEX_PATTERN = ".*?(\(?\d{3}\D{0,3}\d{3}\D{0,3}\d{4}).*?"
EMAIL_ADDRESS_REGEX_PATTERN = (
    "([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"
)


def check_valid_phone_number(phone_number):

    if len(phone_number) > 15:
        return False

    pattern = re.compile(PHONE_NUMBER_REGEX_PATTERN)
    return pattern.match(phone_number)


def check_valid_email_address(email_address):
    pattern = re.compile(EMAIL_ADDRESS_REGEX_PATTERN)
    return pattern.match(email_address)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return (
        str(refresh.access_token),
        str(refresh),
    )


class SignInEndpoint(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            medium = request.data.get("medium", False)
            password = request.data.get("password", False)
    
            ## Raise exception if any of the above are missing
            if not medium or not password:
                capture_message("Sign in endpoint missing medium data")
                return Response(
                    {
                        "error": "Something went wrong. Please try again later or contact the support team."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if medium == "email":
                if not request.data.get(
                    "email", False
                ) or not check_valid_email_address(
                    request.data.get("email").strip().lower()
                ):
                    return Response(
                        {"error": "Please provide a valid email address."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                email = request.data.get("email").strip().lower()
                if email is None:
                    return Response(
                        {"error": "Please provide a valid email address."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                user = User.objects.get(email=email)

            elif medium == "mobile":
                if not request.data.get(
                    "mobile", False
                ) or not check_valid_phone_number(
                    request.data.get("mobile").strip().lower()
                ):
                    return Response(
                        {"error": "Please provide a valid mobile number."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                mobile_number = request.data.get("mobile").strip().lower()
                if mobile_number is None:
                    return Response(
                        {"error": "Please provide a valid mobile number"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                user = User.objects.get(
                    mobile_number=mobile_number
                )

            else:
                capture_message("Sign in endpoint wrong medium data")
                return Response(
                    {
                        "error": "Something went wrong. Please try again later or contact the support team."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # send if it finds two? to logger
            if user is None:
                return Response(
                    {
                        "error": "Sorry, we could not find a user with the provided credentials. Please try again."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not user.check_password(password):
                return Response(
                    {
                        "error": "Sorry, we could not find a user with the provided credentials. Please try again."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            if not user.is_active:
                return Response(
                    {
                        "error": "Your account has been deactivated. Please contact your site administrator."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            serialized_user = UserSerializer(user).data

            # settings last active for the user
            user.last_active = timezone.now()
            user.last_login_time = timezone.now()
            user.last_login_ip = request.META.get("REMOTE_ADDR")
            user.last_login_medium = medium
            user.last_login_uagent = request.META.get("HTTP_USER_AGENT")
            user.token_updated_at = timezone.now()
            user.save()



            access_token, refresh_token = get_tokens_for_user(user)

            data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": serialized_user,
            }

            return Response(data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {
                    "error": "Sorry, we could not find a user with the provided credentials. Please try again."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            capture_exception(e)
            return Response(
                {
                    "error": "Something went wrong. Please try again later or contact the support team."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


# accounts.authentication


# @ratelimit(key="ip", rate="5/h", block=True)
class SignUpEndpoint(APIView):

    permission_classes = [
        AllowAny,
    ]

    def post(self, request):
        try:
            first_name = request.data.get("first_name", "User")
            last_name = request.data.get("last_name", "")

            channel = request.data.get("channel").strip().lower()
            password = request.data.get("password")

            if not channel or not password:
                return Response(
                    {
                        "error": "Something went wrong. Please try again later or contact the support team."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            random_string = uuid.uuid4().hex

            if check_valid_email_address(channel.strip().lower()):
                medium = "email"
            elif check_valid_phone_number(channel.strip().lower()):
                medium = "mobile"
            else:
                capture_message("Invalid medium")
                return Response(
                    {
                        "error": "Something went wrong. Please try again later or contact the support team."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if medium == "email":
                # https://docs.djangoproject.com/en/3.1/ref/models/querysets/#exists
                if User.objects.filter(
                    email=channel.strip().lower()
                ).exists():
                    return Response(
                        {
                            "error": "This email address is already taken. Please try another one."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                username = uuid.uuid4().hex
                user = User(
                    username=username,
                    email=channel.strip().lower(),
                    first_name=first_name,
                    last_name=last_name,
                    mobile_number=random_string,
                )
            elif medium == "mobile":
                if User.objects.filter(
                    mobile_number=channel
                ).exists():
                    return Response(
                        {
                            "error": "This mobile number is already taken. Please try another one."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                username = uuid.uuid4().hex
                user = User(
                    username=username,
                    email=random_string,
                    first_name=first_name,
                    last_name=last_name,
                    mobile_number=channel.strip().lower(),
                )
            else:
                # incase this inbound
                capture_message("Sign up endpoint wrong medium data")
                user = None
                return Response(
                    {
                        "error": "Something went wrong. Please try again later or contact the support team."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(password)
            user.last_active = timezone.now()
            user.last_login_time = timezone.now()
            user.last_login_ip = request.META.get("REMOTE_ADDR")
            user.last_login_medium = medium
            user.last_login_uagent = request.META.get("HTTP_USER_AGENT")
            user.token_updated_at = timezone.now()
            user.save()

            serialized_user = UserSerializer(user).data

            access_token, refresh_token = get_tokens_for_user(user)
            data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": serialized_user,
            }

            return Response(data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(e)
            capture_exception(e)
            return Response(
                {
                    "error": "Something went wrong. Please try again later or contact the support team."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class SignOutEndpoint(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token", False)

            if not refresh_token:
                capture_message("No refresh token provided")
                return Response(
                    {
                        "error": "Something went wrong. Please try again later or contact the support team."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = User.objects.get(pk=request.user.id)

            user.last_logout_time = timezone.now()
            user.last_logout_ip = request.META.get("REMOTE_ADDR")

            user.save()

            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "success"}, status=status.HTTP_200_OK)
        except Exception as e:
            capture_exception(e)
            return Response(
                {
                    "error": "Something went wrong. Please try again later or contact the support team."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
