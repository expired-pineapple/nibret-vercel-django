from rest_framework import serializers
from django.conf import settings

from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email

from dj_rest_auth.registration.serializers import RegisterSerializer

from authentication.models import UserAccount

class CustomRegisterSerializer(RegisterSerializer):
    phone = serializers.CharField(max_length=10, required=True)  # Make it required
    first_name = serializers.CharField(required=True, max_length=5)
    last_name = serializers.CharField(required=True, max_length=100)

    def get_cleaned_data(self):
        return {
            'username': self.validated_data.get('username', ''),
            'password1': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', ''),
            'phone': self.validated_data.get('phone', ''),
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', ''),
            'role': self.validated_data.get('role', 'customer')
        }

    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        
        user.phone = self.cleaned_data.get('phone')
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.role = self.cleaned_data.get('role')
        
        adapter.save_user(request, user, self)
        setup_user_email(request, user, [])
        return user
    

class UserAccountSerialzer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields=['first_name', 'last_name', 'email', 'phone']