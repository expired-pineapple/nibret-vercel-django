from rest_framework import viewsets, status
from rest_framework.response import Response

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

from authentication.models import UserAccount, NotificationClient
from authentication.permissions import CustomerPermission
from authentication.serializers import *


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter 
    client_class = OAuth2Client

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = UserAccount.objects.filter(role='customer')
    serializer_class = UserAccountSerialzer
    permission_classes = [CustomerPermission]


class NotificationClientViewSet(viewsets.ModelViewSet):
    queryset = NotificationClient.objects.all()
    serializer_class = NotificationClientSerializer

    def create(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            data['user'] =  request.user.id
            
            serializer = self.get_serializer(data=data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            notificationClient = serializer.save()
            notificationClient.refresh_from_db()
            serializer = self.get_serializer(notificationClient)

            headers = self.get_success_headers(serializer.data)
            return Response({"detail": serializer.data}, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            print(e)
            return Response(
                {"detail": f"Something went wrong while creating notification client"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
