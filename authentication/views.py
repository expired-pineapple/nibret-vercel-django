from rest_framework import viewsets

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

from authentication.models import UserAccount
from authentication.permissions import CustomerPermission
from authentication.serializers import UserAccountSerialzer


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter 
    client_class = OAuth2Client

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = UserAccount.objects.filter(role='customer')
    serializer_class = UserAccountSerialzer
    permission_classes = [CustomerPermission]