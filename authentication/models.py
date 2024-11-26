from django.db import models, transaction
from django.db.models.signals import post_save
from django.contrib.auth.models import  PermissionsMixin, BaseUserManager, AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.dispatch import receiver
from django.db import models

ROLE_ENUM = (
    ('admin', 'Admin'),
    ('customer', 'Customer'),
    ('agent', 'Agent')
)


CREATE, READ, UPDATE, DELETE = "Create", "View", "Update", "Delete"
LOGIN, LOGOUT, LOGIN_FAILED = "Login", "Logout", "Login Failed"
ACTION_TYPES = [
    (CREATE, CREATE),
    (READ, READ),
    (UPDATE, UPDATE),
    (DELETE, DELETE),
    (LOGIN, LOGIN),
    (LOGOUT, LOGOUT),
    (LOGIN_FAILED, LOGIN_FAILED),
]

SUCCESS, FAILED = "Success", "Failed"
ACTION_STATUS = [(SUCCESS, SUCCESS), (FAILED, FAILED)]

    
class UserManager(BaseUserManager):
    def create_user(self, first_name, last_name,  phone, username, password=None, role="customer", *args, **kwargs):

        user = self.model(username=username, first_name=first_name, last_name=last_name, role=role, phone=phone)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name,last_name,  username, password=None, role='customer',  *args, **kwargs):
        if not username:
            raise ValueError("User must have an username!")
        if not password:
            raise ValueError("User must have a password!")

        user = self.model(first_name=first_name, last_name=last_name, username=username, role=role)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)
        return user


class UserAccount(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    phone=models.CharField(max_length=20, null=True, blank=True)
    password = models.CharField(max_length=128)
    password_changed = models.BooleanField(default=False)
    first_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=150, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_ENUM, default='customer')



    objects = UserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @property
    def name(self):
        return self.first_name + " " +self.last_name

    # @property
    # def is_superuser(self):
    #     return self.role == 'admin'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone']
  



class ActivtyLog(models.Model):
    actor = models.ForeignKey(UserAccount, on_delete=models.CASCADE, null=True)
    action_type = models.CharField(choices=ACTION_TYPES, max_length=15)
    action_time = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)
    status = models.CharField(choices=ACTION_STATUS, max_length=7, default=SUCCESS)
    data = models.JSONField(default=dict)

    # for generic relations
    content_type = models.ForeignKey(
        ContentType, models.SET_NULL, blank=True, null=True
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey()

    def __str__(self) -> str:
        return f"{self.action_type} by {self.actor} on {self.action_time}"