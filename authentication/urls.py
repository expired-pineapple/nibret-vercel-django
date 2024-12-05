from django.urls import include, path, re_path
from rest_framework import routers

from authentication.views import (
    GoogleLogin
)

urlpatterns = [
    path('google/', GoogleLogin.as_view(), name='google_login'),
]