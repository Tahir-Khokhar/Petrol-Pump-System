from django.urls import path

from apps.accounts.views.auth_views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    ProfileView,
    TokenRefreshViewCustom,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('token/refresh/', TokenRefreshViewCustom.as_view(), name='token_refresh'),
]
