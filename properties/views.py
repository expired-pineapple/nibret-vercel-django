from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from properties.serializers import *
from properties.permissions import *


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    # permission_classes = [IsAuthenticated]

class PropertyViewSet(viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    queryset = Property.objects.all() 
    permission_classes = [PropertyPermission]

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'location'
        ).prefetch_related(
            Prefetch(
                'pictures',
            ),
            'amenties',
        )

        filters = {}
        
        property_type = self.request.query_params.get('type')
        if property_type:
            filters['type'] = property_type

        status = self.request.query_params.get("status")
        if status is not None:
            filters['sold_out'] = status.lower() == 'sold'
            if not filters['sold_out']:
                filters['rental'] = status.lower() == "rental" 


        if filters:
            queryset = queryset.filter(**filters)

        return queryset
    @action(detail=False, methods=['post'])
    def search(self, request):
        queryset = Property.objects.all()

        property_type = request.data.get('type')
        if property_type:
            if isinstance(property_type, list):
                queryset = queryset.filter(type__in=property_type)
            else:
                queryset = queryset.filter(type=property_type)

        try:
            min_price = float(request.data.get('min_price')) if request.data.get('min_price') is not None else None
            max_price = float(request.data.get('max_price')) if request.data.get('max_price') is not None else None
        except (ValueError, TypeError):
            min_price = None
            max_price = None

        name = request.data.get('name')
        general_search = request.data.get('search')

        if name:
            queryset = queryset.filter(name__iexact=name)

        if general_search:
            queryset = queryset.filter(
                Q(name__icontains=general_search) | 
                Q(description__icontains=general_search) | 
                Q(location__name__icontains=general_search)
            )

        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        bedroom = request.data.get('bedroom')
        if bedroom and bedroom != "Any":
            queryset = queryset.filter(amenties__bedroom__gte=int(bedroom))

        bathroom = request.data.get('bathroom')
        if bathroom and bathroom != "Any":
            queryset = queryset.filter(amenties__bathroom__gte=int(bathroom))

        area = request.data.get('area')
        if area and area != "Any":
            queryset = queryset.filter(amenties__area__gte=int(area))
            
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        radius = request.data.get('radius', 10) 
        
        if latitude and longitude:
            try:
                radius_degrees = float(radius) / 111  # 1 degree ≈ 111km
                lat = float(latitude)
                lng = float(longitude)
                        
                queryset = queryset.filter(
                    location__latitude__gte=lat - radius_degrees,
                    location__latitude__lte=lat + radius_degrees,
                    location__longitude__gte=lng - radius_degrees,
                    location__longitude__lte=lng + radius_degrees
                )
            except (ValueError, TypeError):
                pass

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    @action(detail=False, methods=['POST'])
    def discount(self, request, pk=None):
        discount={"discount":self.request.data.get("discount")}
        property = Property.objects.filter(pk=self.request.data.get("id")).update(**discount)

        return Response({"detail": "Updated successfully"}, status=status.HTTP_200_OK)
    

    @action(detail=False, methods=['POST'])
    def sold_out(self, request, pk=None):
        property_id = self.request.data.get("id")
        property = Property.objects.filter(pk=property_id).first()

        if property is None:
            return Response({"detail": "Property not found"}, status=status.HTTP_404_NOT_FOUND)

        property.sold_out = not property.sold_out
        property.save()

        return Response({"detail": "Updated successfully"}, status=status.HTTP_200_OK)

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

class LoanersViewSet(viewsets.ModelViewSet):
    queryset = Loaners.objects.all()
    serializer_class = LoanerSerializer


class AuctionViewSet(viewsets.ModelViewSet):
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    
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


class RequestTourViewset(viewsets.ModelViewSet):
    queryset = RequestedTour.objects.all() 
    serializer_class = RequestTourSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        print(self.request.user.role)
        if(self.request.user.role != 'admin'):
            return self.queryset.filter(user=self.request.user)
        else:
            return self.queryset.filter()
   
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def add_items(self, request):
        try:
            item_id = request.data.get('item_id')
            try:
                property_instance = Property.objects.get(id=item_id)
                requested_tour = RequestedTour.objects.create(
                    date = request.data.get('date'),
                    user = request.user,
                    properties = property_instance
                )
                 
            except Property.DoesNotExist:
                    return Response(
                        {"error": f"Property with id {item_id} does not exist."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
         
            return Response(
                RequestTourSerializer(requested_tour).data, 
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

