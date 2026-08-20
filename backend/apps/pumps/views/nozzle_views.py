from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.pumps.filters import NozzleFilter
from apps.pumps.models import Nozzle
from apps.pumps.permissions import IsPumpManagerOrAbove
from apps.pumps.serializers.nozzle_serializers import (
    NozzleListSerializer,
    NozzleMeterUpdateSerializer,
    NozzleSerializer,
)


class NozzleViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for nozzle management.

    - SUPER_ADMIN / PUMP_MANAGER: full create, update, partial_update, destroy
    - All authenticated users: list and retrieve
    """
    queryset = Nozzle.objects.select_related('pump', 'fuel_type').all()
    lookup_field = 'uuid'
    filterset_class = NozzleFilter
    search_fields = ['nozzle_number']
    ordering_fields = ['nozzle_number', 'status', 'created_at', 'updated_at']
    ordering = ['nozzle_number']

    def get_serializer_class(self):
        if self.action == 'list':
            return NozzleListSerializer
        return NozzleSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsPumpManagerOrAbove()]
        return [IsAuthenticated()]

    def get_paginated_response(self, data):
        """Override to include success/message wrapper with pagination metadata."""
        paginator = self.paginator
        return Response({
            'success': True,
            'message': '',
            'data': {
                'count': paginator.page.paginator.count,
                'next': paginator.get_next_link(),
                'previous': paginator.get_previous_link(),
                'results': data,
            },
        }, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        """List nozzles with pagination and filtering."""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Nozzles retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single nozzle by UUID."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Nozzle retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Create a new nozzle. Only SUPER_ADMIN or PUMP_MANAGER."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        nozzle = serializer.save()

        return Response({
            'success': True,
            'message': 'Nozzle created successfully.',
            'data': NozzleSerializer(nozzle).data,
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update a nozzle."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        nozzle = serializer.save()

        return Response({
            'success': True,
            'message': 'Nozzle updated successfully.',
            'data': NozzleSerializer(nozzle).data,
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """Partially update a nozzle."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete a nozzle. Only SUPER_ADMIN or PUMP_MANAGER."""
        instance = self.get_object()
        instance.delete()
        return Response({
            'success': True,
            'message': 'Nozzle deleted successfully.',
            'data': None,
        }, status=status.HTTP_200_OK)


class NozzleMeterUpdateView(APIView):
    """
    POST endpoint to update a nozzle's meter reading.

    Only SUPER_ADMIN and PUMP_MANAGER can update meter readings.
    """
    permission_classes = [IsAuthenticated, IsPumpManagerOrAbove]

    def post(self, request, *args, **kwargs):
        serializer = NozzleMeterUpdateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        nozzle = serializer.save()

        return Response({
            'success': True,
            'message': f'Nozzle {nozzle.nozzle_number} meter updated successfully.',
            'data': NozzleSerializer(nozzle).data,
        }, status=status.HTTP_200_OK)
