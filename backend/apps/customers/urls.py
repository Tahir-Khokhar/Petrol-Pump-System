from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.customers.views.customer_views import CustomerMyProfileView, CustomerViewSet

router = DefaultRouter()
router.register(r'', CustomerViewSet, basename='customer')

urlpatterns = [
    # Custom route before router to avoid UUID pattern collision
    path('my-profile/', CustomerMyProfileView.as_view(), name='customer-my-profile'),
    path('', include(router.urls)),
]
