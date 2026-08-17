from rest_framework import generics, status, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import User
from apps.accounts.serializers.auth_serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    LoginSerializer,
    UserProfileSerializer,
)


class TokenRefreshViewCustom(APIView):
    """
    POST /auth/token/refresh/
    Overrides default to handle missing/deleted users gracefully (401 instead of 500).
    """
    permission_classes = [AllowAny]
    throttle_scope = 'login'

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except InvalidToken as e:
            return Response({
                'success': False,
                'message': 'Token is invalid or expired.',
            }, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User no longer exists.',
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Token refresh failed.',
            }, status=status.HTTP_401_UNAUTHORIZED)

        return Response({
            'success': True,
            'data': {
                'access': str(serializer.validated_data['access']),
                'refresh': str(serializer.validated_data.get('refresh', request.data.get('refresh'))),
            },
        }, status=status.HTTP_200_OK)


class LoginView(APIView):
    """
    POST /auth/login/
    Authenticates a user and returns JWT tokens.
    """
    permission_classes = [AllowAny]
    throttle_scope = 'login'

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Generate JWT tokens with custom claims
        token_serializer = CustomTokenObtainPairSerializer()
        token = token_serializer.get_token(user)

        return Response({
            'success': True,
            'message': 'Login successful.',
            'data': {
                'access': str(token.access_token),
                'refresh': str(token),
                'user': {
                    'uuid': str(user.uuid),
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                    'role_display': user.get_role_display(),
                },
            },
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    POST /auth/logout/
    Blacklists the provided refresh token to effectively log out the user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({
                    'success': False,
                    'message': 'Refresh token is required.',
                }, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({
                'success': True,
                'message': 'Logout successful.',
            }, status=status.HTTP_200_OK)
        except TokenError:
            return Response({
                'success': False,
                'message': 'Token is invalid or expired.',
            }, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """
    GET /auth/profile/
    Returns the authenticated user's profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response({
            'success': True,
            'message': 'Profile retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """
    POST /auth/change-password/
    Allows an authenticated user to change their password.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'success': True,
            'message': 'Password changed successfully. Please log in again.',
        }, status=status.HTTP_200_OK)
