import os

import blurhash
# import google
import json
# import firebase_admin
import numpy as np
import requests

# from firebase_admin import credentials
# from google.oauth2 import service_account
from io import BytesIO
from PIL import Image as pil_image

from properties.models import *

# here = os.path.dirname(os.path.abspath(__file__))
# filename = os.path.join(here, 'service-account.json')
# SCOPES = ['https://www.googleapis.com/auth/firebase.messaging']


def create_property(validated_data):
        location_data = validated_data.pop('location')
        image_data = validated_data.pop('pictures')
        loaners_data = validated_data.pop('loaners', [])
        
        location = Location.objects.create(**location_data)
        

        property = Property.objects.create(location=location, **validated_data)
        
        for image in image_data:
            image['property'] = property
            im = pil_image.open(BytesIO(requests.get(image['image_url']).content))
            im.thumbnail((100,100))
            numpy_image = np.array(im)
            hash = blurhash.encode(numpy_image, components_x=4, components_y=3)
            image['blur_hash'] = hash
            Image.objects.create(**image)
                
        for loaner_data in loaners_data:
            loaner, _ = Loaners.objects.get_or_create(
                name=loaner_data['name'],
                defaults={
                    'logo': loaner_data.get('logo', ''),
                    'real_state_provided': loaner_data.get('real_state_provided', False)
                }
            )
            property.loaners.add(loaner)
        
        return property



# def _get_access_token():
#   credentials = service_account.Credentials.from_service_account_file(
#     filename, scopes=SCOPES)
#   request = google.auth.transport.requests.Request()
#   credentials.refresh(request)
#   return credentials.token

# def notify_user(message):
#   resp = requests.post("https://fcm.googleapis.com/v1/projects/nibret-ca62c/messages:send", 
#     headers={
#         "Authorization": "Bearer " + _get_access_token()
#     },
#     data=json.dumps(message)
#   )

#   if resp.status_code == 200:
#     print('Message sent to Firebase for delivery, response:')
#     print(resp.text)
#   else:
#     print('Unable to send message to Firebase')
#     print(resp.text)
