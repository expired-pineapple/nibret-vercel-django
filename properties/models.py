import uuid
from django.db import models
from math import radians, sin, cos, sqrt, atan2

from authentication.models import UserAccount

class TranslateModel(models.Model):
    name=models.CharField()
    tr_name=models.CharField(null=True, blank=True)
    description=models.TextField(blank=True)
    tr_description=models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True, blank=True)

    class Meta:
        abstract=True
        ordering = ['-created_at']

class HomeOwners(TranslateModel):
    id=models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    type=models.CharField(default="Regular")

    def __str__(self):
        return self.name


    
class Location(TranslateModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    longitude = models.DecimalField(max_digits=25, decimal_places=20)
    latitude = models.DecimalField(max_digits=25, decimal_places=20)

    def __str__(self):
        return self.name
    

    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        R = 6371  
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c

        return distance

    @classmethod
    def find_nearby_places(cls, latitude, longitude, radius_km):
        nearby_places = []
        
        for place in cls.objects.all():
            distance = cls.calculate_distance(
                latitude, 
                longitude,
                place.latitude, 
                place.longitude
            )
            if distance <= radius_km:
                nearby_places.append(
                   place)
                
        return nearby_places
class Property(TranslateModel):

    TYPE_CHOICES = [
        ('Plot Land', 'Plot Land'),
        ('Single Family', 'Single Family'),
        ('Apartment', 'Apartment'),
        ('Penthouse', 'Penthouse'),
        ('Townhouse', 'Townhouse'),
        ('Villa', 'Villa'),
        ('Commercial', 'Commercial'),
        ('Condominium', 'Condominium'),
        ('Office Space', 'Office Space'),
        ('Warehouse', 'Warehouse'),
        ('Luxury Apartment', 'Luxury Apartment')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    location = models.OneToOneField(Location, on_delete=models.CASCADE, related_name='property')
    price = models.FloatField()
    bedroom = models.IntegerField(null=True, blank=True, default=0)
    bathroom = models.IntegerField(null=True, blank=True, default=0)
    area = models.FloatField(null=True, blank=True, default=0)
    currency = models.CharField(max_length=255, default="ETB")
    discount = models.FloatField(null=True, blank=True, default=0)
    sold_out = models.BooleanField(default=False)
    owner = models.ForeignKey(HomeOwners, on_delete=models.CASCADE, related_name='owned_properties', null=True, blank=True)
    is_store = models.BooleanField(default=False)
    type = models.CharField(max_length=255, null=True, blank=True)
    move_in_date = models.DateTimeField(null=True, blank=True)
    rental = models.BooleanField(default=False)
    furnished = models.BooleanField(default=False)
    created_by = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='saved_properties', null=True, blank=True)
    impression_count = models.PositiveIntegerField(default=0, editable=False)

    def increment_impression(self):
        self.impression_count = models.F('impression_count') + 1
        self.save(update_fields=['impression_count'])

    def __str__(self):
        return self.name
    
    class Meta:
       ordering = ['-created_at']



class Loaners(TranslateModel):
   id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
   logo = models.CharField(max_length=255, null=True, blank=True) 
   real_state_provided = models.BooleanField(default=False)
   phone = models.CharField(max_length=255, null=True, blank=True) 

   def __str__(self) -> str:
       return self.name


class HomeLoan(models.Model):
   id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
   property=models.OneToOneField(Property, on_delete=models.CASCADE, related_name="property_loan", null=True, blank=True)
   loan_amount = models.FloatField(default=0.0)
   interest_percentage=models.FloatField(default=0.0)
   loaner = models.ForeignKey(Loaners, on_delete=models.CASCADE,  related_name="loaners")
   
   def __str__(self):
        return f"{self.loaner.name} - {self.property.name}"

class Criteria(models.Model):
   id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
   description = models.TextField()
   loan = models.ForeignKey(HomeLoan, on_delete=models.CASCADE,  related_name="criteria", null=True, blank=True)





class LoanerProperty(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    loaner  = models.ForeignKey(Loaners, on_delete=models.CASCADE, related_name='property')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='loaners', null=True, blank=True)
    description = description = models.TextField(null=True, blank=True)

class SearchHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE,related_name='search_history')
    search_term = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    price = models.FloatField(null=True, blank=True)
    bedroom = models.IntegerField(null=True, blank=True)
    bathroom = models.IntegerField(null=True, blank=True)
    area = models.FloatField(null=True, blank=True)
    sold_out = models.BooleanField(null=True, blank=True)
    is_store = models.BooleanField(null=True, blank=True)
    type = models.CharField(max_length=255, null=True, blank=True)
    move_in_date = models.DateTimeField(null=True, blank=True)
    rental = models.BooleanField(null=True, blank=True)
    furnished = models.BooleanField(null=True, blank=True)
    # test= models.ManyToManyField(Property, related_name="appeared_on_search")
    properties = models.ManyToManyField(Property, related_name="appeared_on_search")



class Image(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    is_cover = models.BooleanField(default=False)
    image_url = models.CharField(max_length=255)
    blur_hash =models.TextField(null=True, blank=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='pictures')

    def __str__(self):
        return f"Image for {self.property.name}"
    

class Auction(TranslateModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    starting_bid = models.FloatField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.OneToOneField(Location, on_delete=models.CASCADE, related_name='auctions')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    

    def __str__(self):
        return f"Auction for {self.name}"

    class Meta:
        verbose_name_plural = "Auctions"


class Wishlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True) 
    user =  models.OneToOneField(UserAccount, on_delete=models.CASCADE, related_name='wishlist')
    property = models.ManyToManyField(Property, related_name='property_wishlist', blank=True) 
    auctions = models.ManyToManyField(Auction, related_name='auction_wishlist', blank=True) 
   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Reviews(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True) 
    rating = models.FloatField(default=0.0)
    user =  models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='reviews')
    properties = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reviews')
    review = models.TextField()

class AuctionImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    is_cover = models.BooleanField(default=False)
    image_url = models.CharField(max_length=255)
    blur_hash = models.CharField(max_length=255, default="blurHash")
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='pictures')


class RequestedTour(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    date = models.DateTimeField()
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='tours')
    properties = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='tours')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Tour saved by {self.user.username}-{self.properties.name}"



class ActivityLog(models.Model):
 
    ACTION_TYPES = (
        (READ, 'View'),
        (CREATE, 'Create'),
        (UPDATE, 'Update'),
        (DELETE, 'Delete'),
    )
    
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activities'
    )
    action_type = models.CharField(max_length=15, choices=ACTION_TYPES)
    status = models.CharField(max_length=7, choices=[(SUCCESS, 'Success'), (FAILED, 'Failed')])
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    object_id = models.UUIDField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['-timestamp']),
        ]