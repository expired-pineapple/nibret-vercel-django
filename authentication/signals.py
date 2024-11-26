
from django.dispatch import receiver
from django.db.models.signals import post_save

from authentication.models import UserAccount
from properties.models import Wishlist


@receiver(post_save, sender=UserAccount)
def create_user_wishlist(sender, instance, created, **kwargs):
    print("Called")
    if created:
        Wishlist.objects.create(user=instance)