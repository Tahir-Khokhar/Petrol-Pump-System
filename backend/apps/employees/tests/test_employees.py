import uuid
import pytest
from datetime import date
from decimal import Decimal

from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.employees.models import Employee
from apps.pumps.models import Pump


# --- Fixtures ---


@pytest.fixture
def super_admin():
    return User.objects.create_superuser(
        email='admin@petropump.com',
        password='AdminPass123',
        first_name='System',
        last_name='Administrator',
    )


@pytest.fixture
def pump_manager():
    user = User.objects.create_user(
        email='manager@petropump.com',
        password='ManagerPass123',
        first_name='Pump',
        last_name='Manager',
        role=User.Role.PUMP_MANAGER,
    )
    user.is_verified = True
    user.save()
    return user


@pytest.fixture
def accountant_user():
    user = User.objects.create_user(
        email='accountant@petropump.com',
        password='AccountantPass123',
        first_name='Bob',
        last_name='Accountant',
        role=User.Role.ACCOUNTANT,
    )
    user.is_verified = True
    user.save()
    return user


@pytest.fixture
def cashier():
    user = User.objects.create_user(
        email='cashier@petropump.com',
        password='CashierPass123',
        first_name='Jane',
        last_name='Cashier',
        role=User.Role.CASHIER,
    )
    user.is_verified = True
    user.save()
    return user


@pytest.fixture
def pump_attendant_user():
    user = User.objects.create_user(
        email='attendant@petropump.com',
        password='AttendantPass123',
        first_name='John',
        last_name='Attendant',
        role=User.Role.PUMP_ATTENDANT,
    )
    user.is_verified = True
    user.save()
    return user


@pytest.fixture
def customer_user():
    user = User.objects.create_user(
        email='customer@petropump.com',
        password='CustomerPass123',
        first_name='Alice',
        last_name='Smith',
        role=User.Role.CUSTOMER,
    )
    user.is_verified = True
    user.save()
    return user


@pytest.fixture
def employee_user():
    """A user without an employee profile for creating a new employee."""
    user = User.objects.create_user(
        email='newemployee@petropump.com',
        password='EmployeePass123',
        first_name='New',
        last_name='Employee',
    )
    user.is_verified = True
    user.save()
    return user


@pytest.fixture
def pump_obj():
    return Pump.objects.create(
        pump_number='PMP-001',
        name='Main Pump',
        location='Front',
    )


@pytest.fixture
def employee(emp_user_for_profile, pump_obj):
    """Create an employee linked to emp_user_for_profile."""
    emp = Employee.objects.create(
        user=emp_user_for_profile,
        employee_id='EMP-001',
        name='Test Employee',
        phone='1234567890',
        email='employee@test.com',
        job_role=Employee.JobRole.CASHIER,
        salary=Decimal('50000.00'),
        hire_date=date(2024, 1, 15),
        assigned_pump=pump_obj,
        status=Employee.Status.ACTIVE,
    )
    return emp


@pytest.fixture
def emp_user_for_profile():
    """User that will be linked to an employee profile."""
    user = User.objects.create_user(
        email='emp@petropump.com',
        password='EmpPass123',
        first_name='Emp',
        last_name='Profile',
        role=User.Role.CASHIER,
    )
    user.is_verified = True
    user.save()
    return user


@pytest.fixture
def auth_client(api_client, super_admin):
    refresh = RefreshToken.for_user(super_admin)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def manager_auth_client(api_client, pump_manager):
    refresh = RefreshToken.for_user(pump_manager)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def cashier_auth_client(api_client, cashier):
    refresh = RefreshToken.for_user(cashier)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def attendant_auth_client(api_client, pump_attendant_user):
    refresh = RefreshToken.for_user(pump_attendant_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def accountant_auth_client(api_client, accountant_user):
    refresh = RefreshToken.for_user(accountant_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def customer_auth_client(api_client, customer_user):
    refresh = RefreshToken.for_user(customer_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def employee_create_data(employee_user, pump_obj):
    return {
        'user': str(employee_user.uuid),
        'employee_id': 'EMP-002',
        'name': 'Jane Doe',
        'phone': '9876543210',
        'email': 'jane@example.com',
        'job_role': 'CASHIER',
        'salary': '45000.00',
        'hire_date': '2024-06-01',
        'assigned_pump': str(pump_obj.uuid),
    }


# --- Employee CRUD Tests ---


@pytest.mark.django_db
class TestEmployeeCRUD:
    """Tests for employee create, read, update, delete."""

    def test_create_employee_success(self, auth_client, employee_create_data):
        response = auth_client.post('/api/v1/employees/', employee_create_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert response.data['data']['employee_id'] == 'EMP-002'
        assert response.data['data']['name'] == 'Jane Doe'
        assert response.data['data']['user']['email'] == 'newemployee@petropump.com'

    def test_create_employee_syncs_user_role(self, auth_client, employee_user, pump_obj):
        """When creating an employee with CASHIER role, user role should be updated to CASHIER."""
        data = {
            'user': str(employee_user.uuid),
            'employee_id': 'EMP-010',
            'name': 'Role Test',
            'job_role': 'PUMP_ATTENDANT',
            'hire_date': '2024-01-01',
        }
        response = auth_client.post('/api/v1/employees/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        employee_user.refresh_from_db()
        assert employee_user.role == User.Role.PUMP_ATTENDANT

    def test_create_employee_manager_allowed(self, manager_auth_client, employee_create_data):
        response = manager_auth_client.post('/api/v1/employees/', employee_create_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_employee_cashier_forbidden(self, cashier_auth_client, employee_create_data):
        response = cashier_auth_client.post('/api/v1/employees/', employee_create_data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_employee_unauthenticated(self, api_client, employee_create_data):
        response = api_client.post('/api/v1/employees/', employee_create_data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_employee_duplicate_employee_id(self, auth_client, employee, employee_user, pump_obj):
        data = {
            'user': str(employee_user.uuid),
            'employee_id': 'EMP-001',  # duplicate
            'name': 'Dup Employee',
            'job_role': 'CASHIER',
            'hire_date': '2024-01-01',
        }
        response = auth_client.post('/api/v1/employees/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_employee_nonexistent_user(self, auth_client, pump_obj):
        data = {
            'user': str(uuid.uuid4()),
            'employee_id': 'EMP-999',
            'name': 'Ghost',
            'job_role': 'CASHIER',
            'hire_date': '2024-01-01',
        }
        response = auth_client.post('/api/v1/employees/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_employee_user_already_has_profile(self, auth_client, employee, employee_user, pump_obj):
        """User already linked to an employee should be rejected."""
        # employee fixture uses emp_user_for_profile; use a different user that has a profile
        data = {
            'user': str(employee.user.uuid),  # already linked to 'employee' fixture
            'employee_id': 'EMP-NEW',
            'name': 'Double Profile',
            'job_role': 'CASHIER',
            'hire_date': '2024-01-01',
        }
        response = auth_client.post('/api/v1/employees/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_employees_empty(self, auth_client):
        response = auth_client.get('/api/v1/employees/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

    def test_list_employees_with_data(self, auth_client, employee):
        response = auth_client.get('/api/v1/employees/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) >= 1
        result = response.data['data'][0]
        assert result['employee_id'] == 'EMP-001'
        assert result['name'] == 'Test Employee'

    def test_retrieve_employee(self, auth_client, employee):
        response = auth_client.get(f'/api/v1/employees/{employee.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['employee_id'] == 'EMP-001'
        assert response.data['data']['user'] is not None
        assert response.data['data']['assigned_pump'] is not None

    def test_retrieve_employee_not_found(self, auth_client):
        response = auth_client.get(f'/api/v1/employees/{uuid.uuid4()}/', format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_employee(self, auth_client, employee):
        data = {'name': 'Updated Name', 'phone': '5555555555'}
        response = auth_client.patch(
            f'/api/v1/employees/{employee.uuid}/', data, format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['name'] == 'Updated Name'
        assert response.data['data']['phone'] == '5555555555'

    def test_delete_employee(self, auth_client, employee):
        response = auth_client.delete(f'/api/v1/employees/{employee.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert Employee.objects.filter(uuid=employee.uuid).count() == 0


# --- Employee Role Access Tests ---


@pytest.mark.django_db
class TestEmployeeRoleAccess:
    """Tests for role-based access to employee endpoints."""

    def test_customer_no_access(self, customer_auth_client, employee):
        response = customer_auth_client.get('/api/v1/employees/', format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cashier_can_list(self, cashier_auth_client, employee):
        response = cashier_auth_client.get('/api/v1/employees/', format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_cashier_can_retrieve(self, cashier_auth_client, employee):
        response = cashier_auth_client.get(f'/api/v1/employees/{employee.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_cashier_cannot_create(self, cashier_auth_client, employee_create_data):
        response = cashier_auth_client.post('/api/v1/employees/', employee_create_data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_pump_attendant_can_list(self, attendant_auth_client, employee):
        response = attendant_auth_client.get('/api/v1/employees/', format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_pump_attendant_can_retrieve(self, attendant_auth_client, employee):
        response = attendant_auth_client.get(f'/api/v1/employees/{employee.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_accountant_can_list(self, accountant_auth_client, employee):
        response = accountant_auth_client.get('/api/v1/employees/', format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_accountant_can_retrieve(self, accountant_auth_client, employee):
        response = accountant_auth_client.get(f'/api/v1/employees/{employee.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_manager_can_crud(self, manager_auth_client, employee_user, pump_obj):
        data = {
            'user': str(employee_user.uuid),
            'employee_id': 'EMP-MGR',
            'name': 'Manager Created',
            'job_role': 'CASHIER',
            'hire_date': '2024-01-01',
        }
        response = manager_auth_client.post('/api/v1/employees/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        emp_uuid = response.data['data']['id']
        # Update
        resp = manager_auth_client.patch(
            f'/api/v1/employees/{emp_uuid}/', {'name': 'Mgr Updated'}, format='json'
        )
        assert resp.status_code == status.HTTP_200_OK
        # Delete
        resp = manager_auth_client.delete(f'/api/v1/employees/{emp_uuid}/', format='json')
        assert resp.status_code == status.HTTP_200_OK


# --- Salary Visibility Tests ---


@pytest.mark.django_db
class TestSalaryVisibility:
    """Tests that salary is hidden for unauthorized roles."""

    def test_admin_sees_salary(self, auth_client, employee):
        response = auth_client.get(f'/api/v1/employees/{employee.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['salary'] is not None
        assert response.data['data']['salary'] == '50000.00'

    def test_manager_sees_salary(self, manager_auth_client, employee):
        response = manager_auth_client.get(f'/api/v1/employees/{employee.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['salary'] is not None
        assert response.data['data']['salary'] == '50000.00'

    def test_accountant_sees_salary(self, accountant_auth_client, employee):
        response = accountant_auth_client.get(f'/api/v1/employees/{employee.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['salary'] is not None
        assert response.data['data']['salary'] == '50000.00'

    def test_cashier_cannot_see_salary(self, cashier_auth_client, employee):
        response = cashier_auth_client.get(f'/api/v1/employees/{employee.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['salary'] is None

    def test_pump_attendant_cannot_see_salary(self, attendant_auth_client, employee):
        response = attendant_auth_client.get(f'/api/v1/employees/{employee.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['salary'] is None

    def test_list_salary_hidden_for_cashier(self, cashier_auth_client, employee):
        response = cashier_auth_client.get('/api/v1/employees/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data'][0]['salary'] is None


# --- Employee Pump Assignment Tests ---


@pytest.mark.django_db
class TestEmployeePumpAssignment:
    """Tests for pump assignment in employee creation/update."""

    def test_create_with_pump(self, auth_client, employee_create_data):
        response = auth_client.post('/api/v1/employees/', employee_create_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['assigned_pump'] is not None
        assert response.data['data']['assigned_pump']['pump_number'] == 'PMP-001'

    def test_create_without_pump(self, auth_client, employee_user):
        data = {
            'user': str(employee_user.uuid),
            'employee_id': 'EMP-NOPUMP',
            'name': 'No Pump',
            'job_role': 'CASHIER',
            'hire_date': '2024-01-01',
        }
        response = auth_client.post('/api/v1/employees/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['assigned_pump'] is None

    def test_update_assign_pump(self, auth_client, employee, pump_obj):
        # First remove pump
        employee.assigned_pump = None
        employee.save()
        data = {'assigned_pump': str(pump_obj.uuid)}
        response = auth_client.patch(
            f'/api/v1/employees/{employee.uuid}/', data, format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['assigned_pump'] is not None

    def test_update_remove_pump(self, auth_client, employee):
        data = {'assigned_pump': None}
        response = auth_client.patch(
            f'/api/v1/employees/{employee.uuid}/', data, format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['assigned_pump'] is None

    def test_create_with_nonexistent_pump(self, auth_client, employee_user):
        data = {
            'user': str(employee_user.uuid),
            'employee_id': 'EMP-BADPUMP',
            'name': 'Bad Pump',
            'job_role': 'CASHIER',
            'hire_date': '2024-01-01',
            'assigned_pump': str(uuid.uuid4()),
        }
        response = auth_client.post('/api/v1/employees/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
