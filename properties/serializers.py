from rest_framework import serializers

from authentication.serializers import UserAccountSerialzer
from .models import AuctionImage, Criteria, HomeLoan, LoanerProperty, Location, Property, Image, Amenties, Auction, Wishlist, Reviews, Loaners


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class LoanersPropertySerializer(serializers.ModelSerializer):
    class Meta: 
        model = LoanerProperty
    

class CriteriaSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Criteria
        fields='__all__'

class ImageSerializer(serializers.ModelSerializer):
    property = serializers.UUIDField(read_only=True)
    class Meta:
        model = Image
        fields = '__all__'

class AmentiesSerializer(serializers.ModelSerializer):
    property = serializers.UUIDField(read_only=True)

    class Meta:
        model = Amenties
        fields = '__all__'

class AuctionSerializer(serializers.ModelSerializer):
    start_date = serializers.SerializerMethodField()
    location = LocationSerializer()
    pictures = ImageSerializer(many=True)
    is_wishlisted = serializers.SerializerMethodField()

    class Meta:
        model = Auction
        fields = '__all__'

    def get_is_wishlisted(self, obj):
        if hasattr(obj, 'is_wishlisted'):
            return obj.is_wishlisted
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Wishlist.objects.filter(
                user=request.user,
                auctions=obj 
            ).exists()
        return False

    def get_start_date(self, obj):
        return obj.start_date.strftime("%Y-%m-%d")

    def create(self, validated_data):
        # Extract nested data
        location_data = validated_data.pop('location')
        pictures_data = validated_data.pop('pictures', [])

        # Create location first
        location = Location.objects.create(**location_data)

        # Create auction with the location
        auction = Auction.objects.create(location=location, **validated_data)

        # Create pictures
        for picture_data in pictures_data:
            AuctionImage.objects.create(auction=auction, **picture_data)

        return auction

    def update(self, instance, validated_data):
        # Handle location update
        if 'location' in validated_data:
            location_data = validated_data.pop('location')
            location = instance.location
            for attr, value in location_data.items():
                setattr(location, attr, value)
            location.save()

        # Handle pictures update
        if 'pictures' in validated_data:
            pictures_data = validated_data.pop('pictures')
            # Optional: Delete existing pictures
            instance.pictures.all().delete()
            # Create new pictures
            for picture_data in pictures_data:
                AuctionImage.objects.create(auction=instance, **picture_data)

        # Update remaining auction fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
    
class LoanerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loaners
        fields = ['id', 'name', 'real_state_provided', 'logo', 'phone']

class LoanerPropertySerializer(serializers.ModelSerializer):
    loaner = LoanerSerializer() 
    
    class Meta:
        model = LoanerProperty
        fields = ['id', 'loaner', 'description']

class PropertySerializer(serializers.ModelSerializer):
    location = LocationSerializer()
    pictures = ImageSerializer(many=True)
    amenties = AmentiesSerializer()
    is_wishlisted = serializers.SerializerMethodField()
    loaner_detail = LoanerPropertySerializer(source='loaners', many=True, read_only=True)
    
    class Meta:
        model = Property
        fields = '__all__'

    def get_is_wishlisted(self, obj):
        if hasattr(obj, 'is_wishlisted'):
            return obj.is_wishlisted
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Wishlist.objects.filter(
                user=request.user,
                property=obj

            ).exists()
        return False

    def create(self, validated_data):
        location_data = validated_data.pop('location')
        amenties_data = validated_data.pop('amenties')
        image_data = validated_data.pop('pictures')
        loaners_data = validated_data.pop('loaners', [])
        
        location = Location.objects.create(**location_data)
        

        property = Property.objects.create(location=location, **validated_data)
        

        amenties_data['property'] = property
        Amenties.objects.create(**amenties_data)


        for image in image_data:
            image['property'] = property
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

def update(self, instance, validated_data):
    if 'pictures' in validated_data:
        pictures_data = validated_data.pop('pictures')

        for picture_data in pictures_data:
            existing_images = Image.objects.filter(image_url=picture_data['image_url'])
            
            if existing_images.exists():
                existing_image = existing_images.first()
                existing_image.blur_hash = picture_data.get('blur_hash', existing_image.blur_hash)
                existing_image.is_cover = picture_data.get('is_cover', existing_image.is_cover)
                existing_image.save()
                
                
                if existing_image not in instance.pictures.all():
                    instance.pictures.add(existing_image)
            else:
               
                new_image = Image.objects.create(
                    property=instance,
                    image_url=picture_data['image_url'],
                    blur_hash=picture_data.get('blur_hash', ''),
                    is_cover=picture_data.get('is_cover', False)
                )
                instance.pictures.add(new_image)

    if 'location' in validated_data:
        location_data = validated_data.pop('location')
        Location.objects.filter(id=instance.location.id).update(**location_data)
    
    if 'amenties' in validated_data:
        amenties_data = validated_data.pop('amenties')
        Amenties.objects.filter(property=instance).update(**amenties_data)
    
    if 'loaners' in validated_data:
        loaners_data = validated_data.pop('loaners')
        instance.loaners.clear()
        for loaner_data in loaners_data:
            loaner, _ = Loaners.objects.get_or_create(
                name=loaner_data['name'],
                defaults={
                    'logo': loaner_data.get('logo', ''),
                    'real_state_provided': loaner_data.get('real_state_provided', False)
                }
            )
            instance.loaners.add(loaner)

    # Update property fields
    for field in validated_data:
        setattr(instance, field, validated_data[field])
    instance.save()

    return instance
    



class WishListSerializer(serializers.ModelSerializer):
    property = PropertySerializer(many=True) 
    auctions = AuctionSerializer(many=True)

    class Meta:
        model = Wishlist
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
      class Meta:
        model = Reviews
        fields = '__all__'


class HomeLoanSerializer(serializers.ModelSerializer):

    loaner = LoanerSerializer()
    criteria = CriteriaSerializer(many=True)

    class Meta:
        model = HomeLoan
        fields = '__all__'

    def create(self, validated_data):
        criterias_data = validated_data.pop('criteria')
        loaner = validated_data.pop('loaner')
        criteria=[]
        loaners=Loaners.objects.create(**loaner)
        home_loan = HomeLoan.objects.create(loaner=loaners, **validated_data)
        for c in criterias_data:
            cr = Criteria.objects.create(**c, loan=home_loan)
            criteria.append(cr)
        return home_loan
    
