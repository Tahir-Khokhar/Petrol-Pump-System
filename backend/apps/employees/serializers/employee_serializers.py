from rest_framework import serializers

from apps.accounts.models import User
from apps.employees.models import Employee


class SalaryVisibilityMixin:
    """
    Mixin to conditionally hide salary field based on requesting user's role.
    Salary is visible only to SUPER_ADMIN, PUMP_MANAGER, ACCOUNTANT.
    """

    SALARY_VISIBLE_ROLES = {
        User.Role.SUPER_ADMIN,
        User.Role.PUMP_MANAGER,
        User.Role.ACCOUNTANT,
    }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.role not in self.SALARY_VISIBLE_ROLES:
                data['salary'] = None
        return data


class UserSummarySerializer(serializers.Serializer):
    """Read-only summary of the related User."""
    uuid = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)


class PumpSummarySerializer(serializers.Serializer):
    """Read-only summary of the assigned Pump."""
    uuid = serializers.UUIDField(read_only=True)
    pump_number = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)


class EmployeeSerializer(SalaryVisibilityMixin, serializers.ModelSerializer):
    """Full serializer for employee detail/retrieve."""
    id = serializers.UUIDField(source='uuid', read_only=True)
    user = serializers.SerializerMethodField()
    assigned_pump = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'uuid', 'user', 'employee_id', 'name', 'phone', 'email',
            'job_role', 'salary', 'hire_date', 'assigned_pump', 'status',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']

    def get_user(self, obj):
        if obj.user:
            return {
                'uuid': str(obj.user.uuid),
                'email': obj.user.email,
                'first_name': obj.user.first_name,
                'last_name': obj.user.last_name,
                'role': obj.user.role,
            }
        return None

    def get_assigned_pump(self, obj):
        if obj.assigned_pump:
            return {
                'uuid': str(obj.assigned_pump.uuid),
                'pump_number': obj.assigned_pump.pump_number,
                'name': obj.assigned_pump.name,
            }
        return None


class EmployeeListSerializer(SalaryVisibilityMixin, serializers.ModelSerializer):
    """Lighter serializer for list views."""
    id = serializers.UUIDField(source='uuid', read_only=True)
    assigned_pump = serializers.SerializerMethodField()
    # Flat fields for frontend convenience
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    role = serializers.CharField(source='job_role', read_only=True)
    is_active = serializers.SerializerMethodField()
    assigned_pump_name = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'name', 'phone', 'job_role',
            'assigned_pump', 'status', 'hire_date', 'salary',
            'first_name', 'last_name', 'role', 'is_active', 'assigned_pump_name',
        ]

    def get_first_name(self, obj):
        return obj.name.split(' ')[0] if obj.name else ''

    def get_last_name(self, obj):
        parts = obj.name.split(' ', 1) if obj.name else []
        return parts[1] if len(parts) > 1 else ''

    def get_is_active(self, obj):
        return obj.status == 'ACTIVE'

    def get_assigned_pump_name(self, obj):
        if obj.assigned_pump:
            return obj.assigned_pump.name or f'Pump #{obj.assigned_pump.pump_number}'
        return None

    def get_assigned_pump(self, obj):
        if obj.assigned_pump:
            return {
                'uuid': str(obj.assigned_pump.uuid),
                'pump_number': obj.assigned_pump.pump_number,
                'name': obj.assigned_pump.name,
            }
        return None


class EmployeeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an employee.

    Accepts either:
      - ``user`` (UUID of an existing User), or
      - ``first_name``, ``last_name``, ``email``, ``password``, ``role`` to
        auto-create a new User.
    """
    user = serializers.UUIDField(
        write_only=True,
        required=False,
        help_text='UUID of the existing User to link. If omitted, a new User '
                   'will be created from first_name/last_name/email/password/role.',
    )
    first_name = serializers.CharField(write_only=True, required=False, default='')
    last_name = serializers.CharField(write_only=True, required=False, default='')
    email = serializers.EmailField(write_only=True, required=False, default='')
    password = serializers.CharField(write_only=True, required=False, default='', allow_blank=True)
    role = serializers.CharField(write_only=True, required=False, default='')
    assigned_pump = serializers.UUIDField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text='UUID of the pump to assign.',
    )

    class Meta:
        model = Employee
        fields = [
            'user', 'first_name', 'last_name', 'email', 'password', 'role',
            'employee_id', 'name', 'phone', 'job_role', 'salary',
            'hire_date', 'assigned_pump',
        ]

    def validate(self, attrs):
        has_user = bool(attrs.get('user'))
        has_user_fields = any(attrs.get(k) for k in ('first_name', 'last_name', 'email'))
        if not has_user and not has_user_fields:
            raise serializers.ValidationError(
                'Either "user" (UUID) or "first_name"/"last_name"/"email" '
                'must be provided to create an employee.',
                code='invalid',
            )
        return attrs

    def validate_user(self, value):
        """Validate that user exists and does not already have an employee profile."""
        try:
            user = User.objects.get(uuid=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                'User with this UUID does not exist.',
                code='does_not_exist',
            )
        if hasattr(user, 'employee_profile'):
            raise serializers.ValidationError(
                'This user already has an employee profile.',
                code='already_exists',
            )
        return value

    def validate_assigned_pump(self, value):
        """Validate that pump exists if provided."""
        if value is not None:
            from apps.pumps.models import Pump
            try:
                Pump.objects.get(uuid=value)
            except Pump.DoesNotExist:
                raise serializers.ValidationError(
                    'Pump with this UUID does not exist.',
                    code='does_not_exist',
                )
        return value

    def create(self, validated_data):
        from apps.pumps.models import Pump

        user_id = validated_data.pop('user', None)
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        email = validated_data.pop('email', '')
        password = validated_data.pop('password', '')
        role = validated_data.pop('role', '')
        pump_id = validated_data.pop('assigned_pump', None)

        if user_id:
            user = User.objects.get(uuid=user_id)
        else:
            user = User.objects.create_user(
                email=email,
                password=password or User.objects.make_random_password(16),
                first_name=first_name,
                last_name=last_name,
                role=role or User.Role.PUMP_ATTENDANT,
                is_verified=True,
            )

        if pump_id:
            validated_data['assigned_pump'] = Pump.objects.get(uuid=pump_id)

        # Build name from first_name + last_name if not explicitly provided
        if not validated_data.get('name'):
            validated_data['name'] = f'{first_name} {last_name}'.strip()

        validated_data['user'] = user
        return Employee.objects.create(**validated_data)


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an employee (all fields optional)."""
    assigned_pump = serializers.UUIDField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text='UUID of the pump to assign.',
    )

    class Meta:
        model = Employee
        fields = [
            'name', 'phone', 'email', 'job_role', 'salary',
            'hire_date', 'assigned_pump', 'status',
        ]
        extra_kwargs = {
            field: {'required': False, 'allow_null': True}
            for field in fields
        }

    def validate_assigned_pump(self, value):
        """Validate that pump exists if provided."""
        if value is not None:
            from apps.pumps.models import Pump
            try:
                Pump.objects.get(uuid=value)
            except Pump.DoesNotExist:
                raise serializers.ValidationError(
                    'Pump with this UUID does not exist.',
                    code='does_not_exist',
                )
        return value
