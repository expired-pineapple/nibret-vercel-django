from allauth.account.adapter import DefaultAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        data = form.cleaned_data
        user.phone = data.get('phone')
        user.first_name = data.get('first_name')
        user.last_name = data.get('last_name')
        user.role = data.get('role')
        if commit:
            user.save()
        return user