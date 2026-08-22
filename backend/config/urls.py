from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse, HttpResponseNotFound
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
import os


FRONTEND_ROOT = os.path.join(settings.BASE_DIR, 'static', 'frontend')


def serve_frontend(request, path='index.html'):
    """Serve React SPA files from static/frontend/."""
    # Security: prevent directory traversal
    safe_path = os.path.normpath(path).lstrip('/')
    safe_path = safe_path.replace('..', '')
    file_path = os.path.join(FRONTEND_ROOT, safe_path)

    # If the exact file exists (JS, CSS, images, favicon etc.), serve it
    if os.path.isfile(file_path):
        return FileResponse(open(file_path, 'rb'))

    # SPA fallback — serve index.html for any unmatched route (React Router)
    index_path = os.path.join(FRONTEND_ROOT, 'index.html')
    if os.path.isfile(index_path):
        return FileResponse(open(index_path, 'rb'), content_type='text/html')

    return HttpResponseNotFound(
        'Frontend not built. Run: cd frontend && npm install && npm run build, '
        'then copy dist/ to backend/static/frontend/'
    )


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/users/', include('apps.accounts.user_urls')),
    path('api/v1/fuel-types/', include('apps.fuel.urls')),
    path('api/v1/tanks/', include('apps.fuel.tank_urls')),
    path('api/v1/pumps/', include('apps.pumps.urls')),
    path('api/v1/nozzles/', include('apps.pumps.nozzle_urls')),
    path('api/v1/customers/', include('apps.customers.urls')),
    path('api/v1/vehicles/', include('apps.customers.vehicle_urls')),
    path('api/v1/employees/', include('apps.employees.urls')),
    path('api/v1/sales/', include('apps.sales.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/suppliers/', include('apps.suppliers.urls')),
    path('api/v1/purchases/', include('apps.purchases.urls')),
    path('api/v1/inventory/', include('apps.inventory.urls')),
    path('api/v1/shifts/', include('apps.shifts.urls')),
    path('api/v1/meter-readings/', include('apps.shifts.meter_urls')),
    path('api/v1/expenses/', include('apps.expenses.urls')),
    path('api/v1/reports/', include('apps.reports.urls')),
    path('api/v1/dashboard/', include('apps.reports.dashboard_urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
    path('api/v1/audit-logs/', include('apps.audit_logs.urls')),
    # Serve React frontend static assets (JS, CSS, images)
    re_path(r'^static/frontend/(?P<path>.*)$', serve_frontend),
    # Serve React app — catch all non-API routes (SPA fallback)
    re_path(r'^(?!api/|admin/).*$', serve_frontend),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
