from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from properties.serializers import *
from properties.permissions import *


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    # permission_classes = [IsAuthenticated]

class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    # permission_classes = [PropertyPermission]


    def get_queryset(self):
        queryset = Property.objects.all()
        
        # Filter by type
        property_type = self.request.query_params.get('type', None)
        if property_type:
            queryset = queryset.filter(type=property_type)

        # Filter by price range
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        name = self.request.query_params.get('name', None)
        general_search = self.request.query_params.get('search', None)
        if name:
            queryset = queryset.filter(name=name)

        if general_search:
            queryset = queryset.filter(Q(name__icontains=general_search) | Q( description__icontains=general_search) | Q(location__name__icontains=general_search))
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        bedroom = self.request.query_params.get('bedroom', None)
        if bedroom and bedroom !="Any":
            queryset = queryset = queryset.filter(amenties__bedroom__gte = int(bedroom))

        bathroom = self.request.query_params.get('bathroom', None)
        if bathroom and bathroom !="Any":
            queryset = queryset = queryset.filter(amenties__bathroom__gte = int(bathroom))
        
        area = self.request.query_params.get('area', None)
        if area and area !="Any":
            queryset = queryset = queryset.filter(amenties__area__gte = int(area))
        
        
        

        # Filter by location
        latitude = self.request.query_params.get('latitude', None)
        longitude = self.request.query_params.get('longitude', None)
        radius = self.request.query_params.get('radius', None)
        if all([latitude, longitude, radius]):
            # Add location-based filtering logic here
            pass

        return queryset

    @action(detail=False, methods=['get'])
    def auctions(self, request, *args, **kwargs):
        auctions = self.get_queryset().filter(is_auction=True)
        serializer = self.get_serializer(auctions, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            data['created_by'] =  request.user.id
            
            serializer = self.get_serializer(data=data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            properties = serializer.save()
            properties.refresh_from_db()
            serializer = self.get_serializer(properties)

            headers = self.get_success_headers(serializer.data)
            return Response({"detail": serializer.data}, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            print(e)
            return Response(
                {"detail": f"Something went wrong while creating property"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class HomeLoanViewSet(viewsets.ModelViewSet):
    queryset=HomeLoan.objects.all()
    serializer_class = HomeLoanSerializer
    # permission_classes = [PropertyPermission]

    def get_queryset(self):
        queryset = HomeLoan.objects.all()
        
        general_search = self.request.query_params.get('search', None)
        if general_search:
            print(general_search)
            queryset = queryset.filter(Q(name__icontains=general_search) | Q( description__icontains=general_search))
        return queryset
    


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    # permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        property_id = request.data.get('property_id')
        images = request.data.get('images', [])
        
        property = get_object_or_404(Property, id=property_id)
        created_images = []

        for image_data in images:
            image_data['property'] = property.id
            serializer = self.get_serializer(data=image_data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            created_images.append(serializer.data)

        return Response(created_images, status=status.HTTP_201_CREATED)

class AmentiesViewSet(viewsets.ModelViewSet):
    queryset = Amenties.objects.all()
    serializer_class = AmentiesSerializer
    permission_classes = [PropertyPermission]

class LoanersViewSet(viewsets.ModelViewSet):
    queryset = Loaners.objects.all()
    serializer_class = LoanerSerializer


class AuctionViewSet(viewsets.ModelViewSet):
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    # permission_classes = [IsAuthenticated]
    def get_queryset(self):
        queryset = Auction.objects.all()
        
        general_search = self.request.query_params.get('search', None)
        if general_search:
            queryset = queryset.filter(Q(name__icontains=general_search) | Q( description__icontains=general_search) | Q(location__name__icontains=general_search))
        return queryset
    
    @action(detail=True, methods=['post'])
    def place_bid(self, request, pk=None):
        auction = self.get_object()
        bid_amount = request.data.get('bid_amount')

        if not bid_amount:
            return Response(
                {'error': 'Bid amount is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if auction.current_bid and bid_amount <= auction.current_bid:
            return Response(
                {'error': 'Bid must be higher than current bid'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if bid_amount < auction.starting_bid:
            return Response(
                {'error': 'Bid must be higher than starting bid'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        auction.current_bid = bid_amount
        auction.save()
        return Response(self.get_serializer(auction).data)

class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.all() 
    serializer_class = WishListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        return Response(WishListSerializer(wishlist).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def add_items(self, request):
        try:
            wishlist = self.get_queryset().first()
            if not wishlist:
                return Response(
                    {"error": "Wishlist does not exist."}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            item_id = request.data.get('item_id')
            is_wishlisted = str(request.data.get('is_wishlisted', 'true')).lower() == 'true'
            is_property = str(request.data.get('is_property', 'true')).lower() == 'true'

            if is_property:
                try:
                    property_instance = Property.objects.get(id=item_id)
                    if is_wishlisted:
                        wishlist.property.add(property_instance)
                    else:
                        wishlist.property.remove(property_instance)
                except Property.DoesNotExist:
                    return Response(
                        {"error": f"Property with id {item_id} does not exist."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                try:
                    auction_instance = Auction.objects.get(id=item_id)
                    if is_wishlisted:
                        wishlist.auctions.add(auction_instance)
                    else:
                        wishlist.auctions.remove(auction_instance)
                except Auction.DoesNotExist:
                    return Response(
                        {"error": f"Auction with id {item_id} does not exist."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            wishlist.refresh_from_db()
            return Response(
                WishListSerializer(wishlist).data, 
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class RequestedTourViewSet(viewsets.ModelViewSet):
    queryset = RequestedTour.objects.all() 
    serializer_class = TourSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id 
        
        print("Request data:", data)
        print("User ID:", request.user.id)

        serializer = self.get_serializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        tour = serializer.save()

        tour.refresh_from_db()
        serializer = self.get_serializer(tour)

        headers = self.get_success_headers(serializer.data)
        return Response({"detail": serializer.data}, status=status.HTTP_201_CREATED, headers=headers)
