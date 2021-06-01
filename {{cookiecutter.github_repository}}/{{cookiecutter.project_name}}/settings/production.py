"""Production settings and globals."""
from .common import * # noqa
import dj_database_url

# Database
DEBUG = False
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': "{{cookiecutter.project_name}}",
        'USER': "",
        'PASSWORD': "",
        'HOST': "",
    }
}

# CORS WHITELIST ON PROD
CORS_ORIGIN_WHITELIST = [
    # "https://example.com",
    # "https://sub.example.com",
    # "http://localhost:8080",
    # "http://127.0.0.1:9000"
]
# Parse database configuration from $DATABASE_URL
DATABASES['default'] = dj_database_url.config()
SITE_ID = 1

# Enable Connection Pooling (if desired)
# DATABASES['default']['ENGINE'] = 'django_postgrespool'

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Allow all host headers
ALLOWED_HOSTS = ['*']

# TODO: Make it FALSE and LIST DOMAINS IN FULL PROD.
CORS_ALLOW_ALL_ORIGINS = True

# Simplified static file serving.
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'