# urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from properties.views import *

router = DefaultRouter()
router.register(r'locations', LocationViewSet)
router.register(r'properties', PropertyViewSet)
router.register(r'images', ImageViewSet)
router.register(r'amenities', AmentiesViewSet)
router.register(r'auctions', AuctionViewSet)
router.register(r'wishlist', WishlistViewSet)
router.register(r'tour', RequestTourViewset)
router.register(r'home-loan', HomeLoanViewSet)

urlpatterns = [
    path('', include(router.urls)),
]