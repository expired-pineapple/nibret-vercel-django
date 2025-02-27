import os

import blurhash
import json
import numpy as np
import requests

from io import BytesIO
from PIL import Image as pil_image
from dotenv import load_dotenv
from properties.models import *


load_dotenv()

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

def notify_user(message):
  resp = requests.post("https://fcm.googleapis.com/v1/projects/nibret-ca62c/messages:send", 
    headers={
        "Authorization": f"Bearer {os.getenv("FCM_ACCESS_TOKEN")}"
    },
    data=json.dumps(message)
  )

  if resp.status_code == 200:
    print('Message sent to Firebase for delivery, response:')
    print(resp.text)
  else:
    print('Unable to send message to Firebase')
    print(resp.text)
