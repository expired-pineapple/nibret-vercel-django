from django.contrib import admin
from django.urls import path, include
from dj_rest_auth.jwt_auth import get_refresh_view
from rest_framework_simplejwt.views import TokenVerifyView
from authentication.urls import urlpatterns as authentication_urls
from properties.urls import urlpatterns as property_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/',  include('dj_rest_auth.urls')),
    path('accounts/',  include(authentication_urls)),
    path('accounts/registration/', include('dj_rest_auth.registration.urls')),
    path('',  include(property_urls)),
]
