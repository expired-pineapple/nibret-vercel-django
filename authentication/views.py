from django.db.models.functions import TruncMonth

from rest_framework import viewsets, status
from rest_framework.decorators import action
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

    @action(detail=False, methods=['GET'])
    def monthly_data(self, request):
        try:
            monthly_data = UserAccount.objects.annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('month')

            labels = []
            series = []
            
            for data in monthly_data:
                labels.append(data['month'].strftime('%B %Y'))
                series.append(data['count'])

            return Response({"detail": {"labels": labels, "series": series}}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"detail": "Something went wrong."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
