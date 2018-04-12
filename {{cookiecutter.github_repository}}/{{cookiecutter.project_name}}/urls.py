"""{{ cookiecutter.project_name }} URL Configuration

"""

from django.contrib import admin
from django.urls import path

# from django.conf import settings
# from django.conf.urls import include, url

urlpatterns = [
    path('admin/', admin.site.urls),
]


# if settings.DEBUG:
#     import debug_toolbar
#     urlpatterns = [
#         url(r'^__debug__/', include(debug_toolbar.urls)),
#     ] + urlpatterns
