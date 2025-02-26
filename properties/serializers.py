from rest_framework import serializers

from authentication.serializers import UserAccountSerialzer
from properties.models import *
from properties.utils import *

class HomeOwnersSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeOwners
        fields = "__all__"

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
        location_data = validated_data.pop('location')
        pictures_data = validated_data.pop('pictures', [])
        location = Location.objects.create(**location_data)
        auction = Auction.objects.create(location=location, **validated_data)
        for picture_data in pictures_data:
            AuctionImage.objects.create(auction=auction, **picture_data)
        return auction

    def update(self, instance, validated_data):
        if 'location' in validated_data:
            location_data = validated_data.pop('location')
            location = instance.location
            for attr, value in location_data.items():
                setattr(location, attr, value)
            location.save()
        if 'pictures' in validated_data:
            pictures_data = validated_data.pop('pictures')
            instance.pictures.all().delete()
            for picture_data in pictures_data:
                AuctionImage.objects.create(auction=instance, **picture_data)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
    
class LoanerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loaners
        fields = "__all__"
class LoanerPropertySerializer(serializers.ModelSerializer):
    loaner = LoanerSerializer() 
    
    class Meta:
        model = LoanerProperty
        fields = "__all__"



class PropertySerializer(serializers.ModelSerializer):
    location = LocationSerializer()
    pictures = ImageSerializer(many=True)
    loaner_detail = LoanerPropertySerializer(source='loaners', many=True, read_only=True)
    is_wishlisted = serializers.SerializerMethodField() 
    num_of_wishlist=serializers.IntegerField(allow_null=True, read_only=True)
    loan_amount = serializers.SerializerMethodField()
    premium = serializers.SerializerMethodField() 
    class Meta:
        model = Property
        fields = '__all__'

    def create(self, validated_data):
        property = create_property(validated_data)
        return property

    def update(self, instance, validated_data):
        if 'location' in validated_data:
            location_data = validated_data.pop('location')
            location = instance.location
            for attr, value in location_data.items():
                setattr(location, attr, value)
                location.save()
        if 'pictures' in validated_data:
            pictures_data = validated_data.pop('pictures')
            instance.pictures.all().delete()
            for picture_data in pictures_data:
                Image.objects.create(property=instance, **picture_data)
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
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            instance.save()
        
        return instance

    def get_premium(self, obj):
        if obj.owner and obj.owner.type.lower() == "premium":
            return True
        return False

    def get_is_wishlisted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Wishlist.objects.filter(
                user=request.user,
                property=obj
            ).exists()
        return False

    def get_loan_amount(self, obj):
        try:
            return obj.property_loan.loan_amount
        except:
            return 0

class PropertyDetailSerializer(PropertySerializer):
    similarProperties = serializers.SerializerMethodField()
    def get_similarProperties(self, obj):
        properties = Property.objects.filter(
            owner=obj.owner
        ).exclude(
            id=obj.id 
        ).distinct()
        
        return PropertySerializer(properties, many=True).data

class WishListSerializer(serializers.ModelSerializer):
    property = PropertySerializer(many=True) 
    auctions = AuctionSerializer(many=True)

    class Meta:
        model = Wishlist
        fields = '__all__'


class SearchHistorySerializer(serializers.ModelSerializer):
    properties = PropertySerializer(many=True) 
    class Meta:
        model = SearchHistory
        fields="__all__"

class ReviewSerializer(serializers.ModelSerializer):
      class Meta:
        model = Reviews
        fields = '__all__'


class HomeLoanSerializer(serializers.ModelSerializer):
    loanerId=serializers.CharField(write_only=True)
    loaner = LoanerSerializer(read_only=True)
    criteria = CriteriaSerializer(many=True)
    property=PropertySerializer(read_only=True)

    class Meta:
        model = HomeLoan
        fields = '__all__'

    def create(self, validated_data):
        criterias_data = validated_data.pop('criteria')
        loaner = validated_data.pop('loanerId')
        property = validated_data.pop('property')
        criteria=[]
        loaners=Loaners.objects.get(pk=loaner)
        createdProperty=create_property(property)
        home_loan = HomeLoan.objects.create(loaner=loaners, **validated_data, property=createdProperty)
        for c in criterias_data:
            cr = Criteria.objects.create(**c, loan=home_loan)
            criteria.append(cr)
        return home_loan
    

class RequestTourSerializer(serializers.ModelSerializer):
    user = UserAccountSerialzer(read_only=True)
    properties = PropertySerializer()
    class Meta:
        model = RequestedTour
        fields = '__all__'
