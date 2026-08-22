from django.urls import path

from apps.reports.views.dashboard_views import dashboard_view

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
]
