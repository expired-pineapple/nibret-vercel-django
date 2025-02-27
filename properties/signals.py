from django.db.models.signals import post_save
from django.dispatch import receiver

from authentication.models import NotificationClient 
from properties.models import Property, SearchHistory
from properties.utils import notify_user

@receiver(post_save, sender=Property)
def send_notifications(sender, instance,created=False, **kwargs):
   if created:
      property_type = instance.type
      search_history = SearchHistory.objects.filter(type=property_type)
      # 
      for search in search_history:
         notification_client = NotificationClient.objects.filter(user=search.user).distinct()
         print("HERE",notification_client)
         if len(notification_client) > 0:
            notfication_message = {
               "message":{
                  "token": notification_client[0].fcm_token,
                  "notification":{
                  "body":f"Check out new {property_type} properties",
                  "title":"Explore properties"
                  }
               }
            }
               
            notify_user(notfication_message)
      
