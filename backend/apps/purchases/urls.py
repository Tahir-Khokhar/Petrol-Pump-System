from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.purchases.views.purchase_views import PurchaseViewSet

router = DefaultRouter()
router.register(r'purchases', PurchaseViewSet, basename='purchase')

urlpatterns = [
    path('', include(router.urls)),
]
