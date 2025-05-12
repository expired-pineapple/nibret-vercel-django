from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch, Count, Sum
from django.db.models.functions import TruncMonth


from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from geopy.distance import great_circle

from authentication.permissions import CustomerPermission
from properties.serializers import *
from properties.permissions import *

def get_latlng_bounderies(lat, lng, distance):
    """
    Return min/max lat/lng values for a distance around a latlng.
    :lat:, :lng: the center of the area.
    :distance: in km, the "radius" around the center point.
    :returns: Two corner points of a square that countains the circle,
              lat_min, lng_min, lat_max, lng_max.
    """
    gc = great_circle(kilometers=distance)
    p0 = gc.destination((lat, lng), 0)
    p90 = gc.destination((lat, lng), 90)
    p180 = gc.destination((lat, lng), 180)
    p270 = gc.destination((lat, lng), 270)

    ret = p180[0], p270[1], p0[0], p90[1]
    return ret


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    # permission_classes = [IsAuthenticated]

class PropertyViewSet(UserLogMixin, viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    queryset = Property.objects.filter(Q(property_loan=None)).select_related(
            'location',
           
            
        ).prefetch_related(
            
              'pictures',
        )
    log_message = "Property interaction"
    # permission_classes = [PropertyPermission]
    action_serializers = {
        'retrieve': PropertyDetailSerializer,  
        'list': PropertySerializer,  
    }

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        if request.user.is_authenticated:
            self.get_object().increment_impression()
        return response
        
    def get_serializer_class(self):

        if hasattr(self, 'action_serializers'):
            return self.action_serializers.get(self.action, self.serializer_class)

        return super(PropertyViewSet, self).get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset()

        filters = {}
 
        property_type = self.request.query_params.get('type')
        if property_type and property_type != "All":
            filters['type'] = property_type

        status = self.request.query_params.get("status")
        print(status)
        if status is not None:
            filters['sold_out'] = status.lower() == 'sold'
            if not filters['sold_out']:
                filters['rental'] = status.lower() == "rental" 

        general_search = self.request.query_params.get('search')
        if general_search:
                queryset = queryset.filter(
                    Q(name__icontains=general_search) | 
                    Q(description__icontains=general_search) | 
                    Q(location__name__icontains=general_search)
                )

        if filters:
            queryset = queryset.filter(**filters)

        return queryset

    @action(detail=False, methods=['post'])
    def map_bounds(self, request):
        queryset = super().get_queryset()
        min_latitude=float(request.data.get('min_latitude'))
        min_longitude=float(request.data.get('min_longitude'))
        max_longitude = float(request.data.get('max_longitude'))
        max_latitude = float(request.data.get('max_latitude'))

        queryset = queryset.filter(
                    Q(location__latitude__gte=min_latitude, location__longitude__gte=min_longitude) |
                    Q(location__latitude__lte=max_longitude,location__longitude__lte=max_longitude)
                )

        queryset = queryset.filter(Q(location__in=nearby_places))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def map(self, request):
        queryset = super().get_queryset()
        longitude = float(request.data.get('longitude'))
        latitude = float(request.data.get('latitude'))
        radius = float(request.GET.get('radius', 2.5))
        bounds = get_latlng_bounderies(latitude, longitude, radius)
    
        nearby_places = Location.find_nearby_places(latitude, longitude, radius)

        queryset = queryset.filter(
                    Q(location__latitude__gte=bounds[0], location__longitude__gte=bounds[1]) |
                    Q(location__latitude__lte=bounds[2],location__longitude__lte=bounds[3])
                )

        queryset = queryset.filter(Q(location__in=nearby_places))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def premium(self, request):
        queryset = Property.objects.filter(Q(owner__type__in=['premium', 'Premium']))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['GET'])
    def monthly_data(self, request):
        try:
            monthly_data = Property.objects.annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('month')

            labels = []
            series = []
            
            for data in monthly_data:
                labels.append(data['month'].strftime('%B %Y'))
                series.append(data['count'])

            return Response({"detail": {"labels": labels, "series": series}}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"detail": "Something went wrong."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=False, methods=['GET'])
    def chart_data(self, request):
        try:
            labels=[
                'Luxury Apartment',
                'Apartment',
                'Office Space',
                'Single Family',
                'Condominium', 
                'Plot Land',
                'Penthouse',
                'Townhouse',
                'Villa',
                'Commercial',
                'Warehouse'
            ]
            series = []
            for label in labels:
                series.append(len(Property.objects.filter(type=label)))


            return Response({"detail":{"labels":labels, "series":series}}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e) 
            return Response({"detail": "Something went wrong."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['GET'])
    def loanable(self, request, pk=None):
        property = get_object_or_404(Property, pk=pk)
        serializer = self.get_serializer(property)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @action(detail=False, methods=['get'], permission_classes=[CustomerPermission])
    def admin(self, request):
        try:
            properties = Property.objects.annotate(
                num_of_wishlist=Count("property_wishlist")
            ).order_by('-num_of_wishlist')
            first_property = properties.first()
            total_count = properties.aggregate(
                wishlistedPropertiesCount=Sum("num_of_wishlist")
            )

            page = self.paginate_queryset(properties)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                most_wishlisted = self.get_serializer(first_property)
                return self.get_paginated_response({
                    "properties": serializer.data,
                    "mostWishlisted": most_wishlisted.data,
                    **total_count
                })
                
            return Response({"detail": "Invalid pagination"}, 
                        status=status.HTTP_400_BAD_REQUEST)
                        
        except Exception as e:
            print(e)  
            return Response(
                {"detail": "Something went wrong."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            

    @action(detail=False, methods=['post'])
    def search(self, request):
        try:
            queryset = super().get_queryset()

            filter = Q()
            print(request.data)
            property_type = request.data.get('type')
            min_price = float(request.data.get('min_price')) if request.data.get('min_price') is not None else None
            max_price = float(request.data.get('max_price')) if request.data.get('max_price') is not None else None
            bedrooms = request.data.get('bedroom')
            bathrooms = request.data.get('bathroom')
            property_status = request.data.get('status')
            furnished = request.data.get('furnished')
            general_search = request.data.get('search')
            if general_search:
                queryset = queryset.filter(
                    Q(name__icontains=general_search) | 
                    Q(description__icontains=general_search) | 
                    Q(location__name__icontains=general_search)
                )

            if property_type and property_type != "All":
                filter = Q(type__in = property_type)
            
            if min_price is not None:
                filter &= Q(price__gte = min_price)

            if max_price is not None or max_price==0:
                filter &= Q(price__lte = max_price)
            if bedrooms:
                filter &= Q(bedroom = bedrooms)
            if bathrooms:
                filter &= Q(bathroom = bathrooms)
            if property_status:
                filter &= Q(sold_out = property_status.lower() == 'sold')
                if not property_status.lower() == 'sold':
                    filter &= Q(rental = property_status.lower() == "rental")
            if furnished:
                filter &= Q(furnished = furnished)
            queryset = queryset.filter(filter)
            print(queryset)
            serializer = self.get_serializer(queryset, many=True)
            print(self.request.user)
            if self.request.user.is_authenticated:
                search_history = SearchHistory.objects.create(
                    search_term=general_search,
                    user = self.request.user,
                    bedroom = bedrooms,
                    bathroom = bathrooms,
                    sold_out = property_status.lower() == 'sold' if property_status else "",
                    type = property_type,
                    rental = property_status.lower() == "rental" if property_status else "",
                    furnished = furnished
                )
                for q in queryset:
                    search_history.properties.add(q.id)

            return Response(serializer.data)
        
        except Exception as e:
            print(e) 
            return Response({"detail": "Something went wrong."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['POST'])
    def discount(self, request, pk=None):
        discount={"discount":self.request.data.get("discount")}
        property = Property.objects.filter(pk=self.request.data.get("id")).update(**discount)

        return Response({"detail": "Updated successfully"}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['GET'])
    def property_count(self, request):
        properties = Property.objects.annotate(num_of_wishlist = Count("property_wishlist")).order_by('-num_of_wishlist')
        print(properties.first())
        serializer = self.get_serializer(properties, many=True)
        return Response({"detail":serializer.data}, status=status.HTTP_200_OK)
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
        if self.request.user.role == 'customer':
            return self.queryset.filter(user=self.request.user)
        return self.queryset.all()

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


    @action(detail=True, methods=['get'], permission_classes=[CustomerPermission])
    def customer_wishlists(self, requests, pk):
        print( self.queryset.all())
        wishlists = self.queryset.filter(user=pk)
        data = self.get_serializer(wishlists, many=True).data
        return  Response(
                data, 
                status=status.HTTP_200_OK
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



class SearchHistoryViewset(viewsets.ModelViewSet):
    queryset = SearchHistory.objects.all() 
    serializer_class = SearchHistorySerializer
    permission_classes = [AdminReadOnly]

    @action(detail=True, methods=['get'])
    def customer(self, requests, pk):
        print( self.queryset.all())
        search_history = self.queryset.filter(user=pk)
        data = self.get_serializer(search_history, many=True).data
        return  Response(
                data, 
                status=status.HTTP_200_OK
            )

class HomeOwnerViewSet(viewsets.ModelViewSet):
    queryset=HomeOwners.objects.all()
    serializer_class=HomeOwnersSerializer
    permission_classes=[PropertyPermission]
