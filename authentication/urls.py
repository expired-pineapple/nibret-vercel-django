from django.urls import include, path, re_path
from rest_framework import routers
from rest_framework.routers import DefaultRouter

from authentication.views import (
    CustomerViewSet,
    GoogleLogin
)

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)

urlpatterns = [
    path('google/', GoogleLogin.as_view(), name='google_login'),
    path('', include(router.urls))
]