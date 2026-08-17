import random
import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from faker import Faker

from apps.fuel.models import FuelType, Tank
from apps.pumps.models import Pump, Nozzle, PumpFuelType
from apps.customers.models import Customer, Vehicle
from apps.employees.models import Employee
from apps.suppliers.models import Supplier
from apps.inventory.models import InventoryItem, InventoryTransaction
from apps.sales.models import Sale
from apps.payments.models import Payment
from apps.purchases.models import Purchase
from apps.expenses.models import Expense
from apps.shifts.models import Shift, MeterReading

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Generate realistic demo data for the Petrol Pump Management System'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')

    def handle(self, *args, **options):
        if options['clear']:
            confirm = input('This will DELETE all existing data. Type "yes" to confirm: ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Aborted.'))
                return
            self._clear_data()

        self.stdout.write(self.style.SUCCESS('Creating demo data...'))
        with transaction.atomic():
            self._create_users()
            self._create_fuel_types()
            self._create_tanks()
            self._create_pumps_and_nozzles()
            self._create_employees()
            self._create_suppliers()
            self._create_customers_and_vehicles()
            self._create_purchases()
            self._create_inventory_items()
            self._create_shifts()
            self._create_sales()
            self._create_expenses()

        self.stdout.write(self.style.SUCCESS('Demo data created successfully!'))
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('  Super Admin: admin@petrolpump.com / admin123')
        self.stdout.write('  Manager:     manager@petrolpump.com / manager123')
        self.stdout.write('  Cashier:    cashier1@petrolpump.com / cashier123')

    def _clear_data(self):
        self.stdout.write('Clearing existing data...')
        models_to_clear = [
            MeterReading, Shift, Expense, Sale, Payment,
            InventoryTransaction, InventoryItem, Purchase,
            Supplier, Vehicle, Customer, Employee,
            Nozzle, PumpFuelType, Pump, Tank, FuelType, User,
        ]
        for model in models_to_clear:
            model.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Data cleared.'))

    def _create_users(self):
        self.stdout.write('Creating users...')
        users_data = [
            {'email': 'admin@petrolpump.com', 'first_name': 'System', 'last_name': 'Admin',
             'role': User.Role.SUPER_ADMIN, 'password': 'admin123', 'is_staff': True, 'is_superuser': True},
            {'email': 'manager@petrolpump.com', 'first_name': 'Ahmed', 'last_name': 'Khan',
             'role': User.Role.PUMP_MANAGER, 'password': 'manager123'},
            {'email': 'manager2@petrolpump.com', 'first_name': 'Ali', 'last_name': 'Hassan',
             'role': User.Role.PUMP_MANAGER, 'password': 'manager123'},
            {'email': 'cashier1@petrolpump.com', 'first_name': 'Sara', 'last_name': 'Ali',
             'role': User.Role.CASHIER, 'password': 'cashier123'},
            {'email': 'cashier2@petrolpump.com', 'first_name': 'Fatima', 'last_name': 'Zahra',
             'role': User.Role.CASHIER, 'password': 'cashier123'},
            {'email': 'cashier3@petrolpump.com', 'first_name': 'Hina', 'last_name': 'Begum',
             'role': User.Role.CASHIER, 'password': 'cashier123'},
            {'email': 'cashier4@petrolpump.com', 'first_name': 'Ayesha', 'last_name': 'Khan',
             'role': User.Role.CASHIER, 'password': 'cashier123'},
            {'email': 'cashier5@petrolpump.com', 'first_name': 'Nida', 'last_name': 'Raza',
             'role': User.Role.CASHIER, 'password': 'cashier123'},
            {'email': 'attendant1@petrolpump.com', 'first_name': 'Imran', 'last_name': 'Sheikh',
             'role': User.Role.PUMP_ATTENDANT, 'password': 'attendant123'},
            {'email': 'attendant2@petrolpump.com', 'first_name': 'Kamran', 'last_name': 'Raza',
             'role': User.Role.PUMP_ATTENDANT, 'password': 'attendant123'},
            {'email': 'attendant3@petrolpump.com', 'first_name': 'Usman', 'last_name': 'Malik',
             'role': User.Role.PUMP_ATTENDANT, 'password': 'attendant123'},
            {'email': 'attendant4@petrolpump.com', 'first_name': 'Bilal', 'last_name': 'Siddiqui',
             'role': User.Role.PUMP_ATTENDANT, 'password': 'attendant123'},
            {'email': 'attendant5@petrolpump.com', 'first_name': 'Hamza', 'last_name': 'Tarar',
             'role': User.Role.PUMP_ATTENDANT, 'password': 'attendant123'},
            {'email': 'attendant6@petrolpump.com', 'first_name': 'Tariq', 'last_name': 'Jamal',
             'role': User.Role.PUMP_ATTENDANT, 'password': 'attendant123'},
            {'email': 'attendant7@petrolpump.com', 'first_name': 'Waqar', 'last_name': 'Hussain',
             'role': User.Role.PUMP_ATTENDANT, 'password': 'attendant123'},
            {'email': 'attendant8@petrolpump.com', 'first_name': 'Nasir', 'last_name': 'Iqbal',
             'role': User.Role.PUMP_ATTENDANT, 'password': 'attendant123'},
            {'email': 'attendant9@petrolpump.com', 'first_name': 'Sajid', 'last_name': 'Hussain',
             'role': User.Role.PUMP_ATTENDANT, 'password': 'attendant123'},
            {'email': 'attendant10@petrolpump.com', 'first_name': 'Asif', 'last_name': 'Mehmood',
             'role': User.Role.PUMP_ATTENDANT, 'password': 'attendant123'},
            {'email': 'inventory1@petrolpump.com', 'first_name': 'Rizwan', 'last_name': 'Ahmed',
             'role': User.Role.INVENTORY_MANAGER, 'password': 'inventory123'},
            {'email': 'inventory2@petrolpump.com', 'first_name': 'Faisal', 'last_name': 'Nawaz',
             'role': User.Role.INVENTORY_MANAGER, 'password': 'inventory123'},
            {'email': 'accountant1@petrolpump.com', 'first_name': 'Zubair', 'last_name': 'Khan',
             'role': User.Role.ACCOUNTANT, 'password': 'accountant123'},
            {'email': 'accountant2@petrolpump.com', 'first_name': 'Tahir', 'last_name': 'Abbas',
             'role': User.Role.ACCOUNTANT, 'password': 'accountant123'},
        ]
        self._users = []
        for ud in users_data:
            user = User.objects.create_user(
                email=ud['email'],
                password=ud['password'],
                first_name=ud['first_name'],
                last_name=ud['last_name'],
                role=ud['role'],
                is_staff=ud.get('is_staff', False),
                is_superuser=ud.get('is_superuser', False),
                is_verified=True,
            )
            self._users.append(user)
        self.stdout.write(f'  Created {len(self._users)} users')

    def _create_fuel_types(self):
        self.stdout.write('Creating fuel types...')
        fuel_data = [
            {'name': 'Petrol', 'code': 'PET', 'description': 'Regular petrol', 'unit': 'Liter',
             'current_price': Decimal('275.00'), 'minimum_stock_level': Decimal('2000')},
            {'name': 'High-Octane', 'code': 'HOBC', 'description': 'High octane blended compound', 'unit': 'Liter',
             'current_price': Decimal('310.00'), 'minimum_stock_level': Decimal('1000')},
            {'name': 'Diesel', 'code': 'DSL', 'description': 'High speed diesel', 'unit': 'Liter',
             'current_price': Decimal('290.00'), 'minimum_stock_level': Decimal('2000')},
            {'name': 'CNG', 'code': 'CNG', 'description': 'Compressed natural gas', 'unit': 'Kg',
             'current_price': Decimal('210.00'), 'minimum_stock_level': Decimal('500')},
        ]
        self._fuel_types = []
        for fd in fuel_data:
            ft = FuelType.objects.create(**fd)
            self._fuel_types.append(ft)
        self.stdout.write(f'  Created {len(self._fuel_types)} fuel types')

    def _create_tanks(self):
        self.stdout.write('Creating tanks...')
        tank_data = [
            {'tank_number': 'TK-001', 'fuel_type': self._fuel_types[0], 'capacity': Decimal('20000'),
             'current_quantity': Decimal('15000'), 'minimum_quantity': Decimal('2000'), 'location': 'Underground A'},
            {'tank_number': 'TK-002', 'fuel_type': self._fuel_types[1], 'capacity': Decimal('10000'),
             'current_quantity': Decimal('7500'), 'minimum_quantity': Decimal('1000'), 'location': 'Underground B'},
            {'tank_number': 'TK-003', 'fuel_type': self._fuel_types[2], 'capacity': Decimal('15000'),
             'current_quantity': Decimal('12000'), 'minimum_quantity': Decimal('2000'), 'location': 'Underground C'},
            {'tank_number': 'TK-004', 'fuel_type': self._fuel_types[3], 'capacity': Decimal('5000'),
             'current_quantity': Decimal('3500'), 'minimum_quantity': Decimal('500'), 'location': 'Above Ground A'},
        ]
        self._tanks = []
        for td in tank_data:
            tank = Tank.objects.create(**td)
            self._tanks.append(tank)
        self.stdout.write(f'  Created {len(self._tanks)} tanks')

    def _create_pumps_and_nozzles(self):
        self.stdout.write('Creating pumps and nozzles...')
        pump_configs = [
            {'pump_number': 'PMP-001', 'name': 'Pump 1 - Main', 'location': 'Front Left',
             'fuel_type_indices': [0, 2], 'attendant_idx': 8},
            {'pump_number': 'PMP-002', 'name': 'Pump 2 - Main', 'location': 'Front Right',
             'fuel_type_indices': [0, 2], 'attendant_idx': 9},
            {'pump_number': 'PMP-003', 'name': 'Pump 3 - Side', 'location': 'Side Left',
             'fuel_type_indices': [1, 2], 'attendant_idx': 10},
            {'pump_number': 'PMP-004', 'name': 'Pump 4 - Side', 'location': 'Side Right',
             'fuel_type_indices': [0, 1], 'attendant_idx': 11},
            {'pump_number': 'PMP-005', 'name': 'Pump 5 - Rear', 'location': 'Rear Left',
             'fuel_type_indices': [0, 2, 3], 'attendant_idx': 12},
            {'pump_number': 'PMP-006', 'name': 'Pump 6 - Rear', 'location': 'Rear Right',
             'fuel_type_indices': [1, 3], 'attendant_idx': 13},
        ]
        self._pumps = []
        self._nozzles = []
        nozzle_counter = 1
        for pc in pump_configs:
            attendant = self._users[pc['attendant_idx']]
            pump = Pump.objects.create(
                pump_number=pc['pump_number'],
                name=pc['name'],
                location=pc['location'],
                status='ACTIVE',
                assigned_employee=attendant,
                installation_date=fake.date_between(start_date='-3y', end_date='-1y'),
                last_maintenance_date=fake.date_between(start_date='-3m', end_date='-1d'),
            )
            for fi in pc['fuel_type_indices']:
                ft = self._fuel_types[fi]
                PumpFuelType.objects.create(pump=pump, fuel_type=ft)
                nozzle = Nozzle.objects.create(
                    nozzle_number=f'NZL-{nozzle_counter:03d}',
                    pump=pump,
                    fuel_type=ft,
                    opening_meter_reading=Decimal('0'),
                    current_meter_reading=Decimal('0'),
                    status='ACTIVE',
                )
                self._nozzles.append(nozzle)
                nozzle_counter += 1
            self._pumps.append(pump)
        self.stdout.write(f'  Created {len(self._pumps)} pumps, {len(self._nozzles)} nozzles')

    def _create_employees(self):
        self.stdout.write('Creating employees...')
        self._employees = []
        emp_configs = [
            (1, 'EMP-001', 'MANAGER', None, Decimal('150000')),
            (2, 'EMP-002', 'MANAGER', None, Decimal('140000')),
            (3, 'EMP-003', 'CASHIER', self._pumps[0], Decimal('60000')),
            (4, 'EMP-004', 'CASHIER', self._pumps[1], Decimal('55000')),
            (5, 'EMP-005', 'CASHIER', self._pumps[2], Decimal('58000')),
            (6, 'EMP-006', 'CASHIER', None, Decimal('56000')),
            (7, 'EMP-007', 'CASHIER', None, Decimal('52000')),
            (18, 'EMP-008', 'INVENTORY_MANAGER', None, Decimal('80000')),
            (19, 'EMP-009', 'INVENTORY_MANAGER', None, Decimal('75000')),
            (20, 'EMP-010', 'ACCOUNTANT', None, Decimal('90000')),
            (21, 'EMP-011', 'ACCOUNTANT', None, Decimal('85000')),
            (8, 'EMP-012', 'PUMP_ATTENDANT', self._pumps[0], Decimal('35000')),
            (9, 'EMP-013', 'PUMP_ATTENDANT', self._pumps[1], Decimal('35000')),
            (10, 'EMP-014', 'PUMP_ATTENDANT', self._pumps[2], Decimal('33000')),
            (11, 'EMP-015', 'PUMP_ATTENDANT', self._pumps[3], Decimal('33000')),
            (12, 'EMP-016', 'PUMP_ATTENDANT', self._pumps[4], Decimal('34000')),
            (13, 'EMP-017', 'PUMP_ATTENDANT', self._pumps[5], Decimal('34000')),
        ]
        for user_idx, emp_id, role, pump, salary in emp_configs:
            user = self._users[user_idx]
            Employee.objects.create(
                user=user,
                employee_id=emp_id,
                name=f'{user.first_name} {user.last_name}',
                phone=fake.phone_number()[:20],
                email=user.email,
                job_role=role,
                salary=salary,
                hire_date=fake.date_between(start_date='-2y', end_date='-1m'),
                assigned_pump=pump,
                status='ACTIVE',
            )
        self.stdout.write(f'  Created {len(emp_configs)} employees')

    def _create_suppliers(self):
        self.stdout.write('Creating suppliers...')
        supplier_data = [
            {'company_name': 'Pakistan State Oil', 'contact_person': 'Tariq Mehmood',
             'phone': '021-99210000', 'email': 'supply@psocom.pk',
             'address': 'PSO House, Karachi', 'tax_number': 'NTN-1234567-1'},
            {'company_name': 'Shell Pakistan', 'contact_person': 'Farhan Ali',
             'phone': '021-99215000', 'email': 'supply@shell.pk',
             'address': 'Shell Pakistan Ltd, Lahore', 'tax_number': 'NTN-2345678-2'},
            {'company_name': 'Total Energies', 'contact_person': 'Omar Siddiqui',
             'phone': '042-35760000', 'email': 'orders@totalenergies.pk',
             'address': 'Total Energies Marketing PK, Islamabad', 'tax_number': 'NTN-3456789-3'},
            {'company_name': 'Caltex Lubricants', 'contact_person': 'Rizwan Ahmed',
             'phone': '021-99218000', 'email': 'orders@caltex.pk',
             'address': 'Caltex House, Faisalabad', 'tax_number': 'NTN-4567890-4'},
            {'company_name': 'Auto Parts Express', 'contact_person': 'Naveed Anwar',
             'phone': '042-36801000', 'email': 'sales@autoparts.pk',
             'address': 'Mall Road, Lahore', 'tax_number': 'NTN-5678901-5'},
        ]
        self._suppliers = []
        for sd in supplier_data:
            supplier = Supplier.objects.create(**sd)
            self._suppliers.append(supplier)
        self.stdout.write(f'  Created {len(self._suppliers)} suppliers')

    def _create_customers_and_vehicles(self):
        self.stdout.write('Creating customers and vehicles...')
        corporate_data = [
            {'full_name': 'TransPort Logistics', 'company_name': 'TransPort Logistics Pvt Ltd',
             'phone': '0300-1234567', 'email': 'accounts@transport.pk',
             'address': 'Industrial Area, Lahore', 'tax_number': 'NTN-9876543',
             'is_corporate': True, 'credit_limit': Decimal('500000')},
            {'full_name': 'City Cab Services', 'company_name': 'City Cab Services (Pvt) Ltd',
             'phone': '0301-2345678', 'email': 'finance@citycab.pk',
             'address': 'Blue Area, Islamabad', 'tax_number': 'NTN-8765432',
             'is_corporate': True, 'credit_limit': Decimal('300000')},
            {'full_name': 'Food Delivery Fleet', 'company_name': 'Food Express Fleet',
             'phone': '0302-3456789', 'email': 'ops@foodexpress.pk',
             'address': 'Gulberg III, Lahore', 'tax_number': 'NTN-7654321',
             'is_corporate': True, 'credit_limit': Decimal('200000')},
        ]
        self._customers = []
        for cd in corporate_data:
            customer = Customer.objects.create(**cd)
            self._customers.append(customer)

        for i in range(47):
            customer = Customer.objects.create(
                full_name=fake.name(),
                phone=fake.phone_number()[:20],
                email=fake.email() if random.random() > 0.3 else '',
                address=fake.address(),
                is_corporate=False,
            )
            self._customers.append(customer)

        vehicle_types = ['CAR', 'MOTORCYCLE', 'TRUCK', 'VAN', 'OTHER']
        vehicle_count = 0
        for customer in self._customers:
            num_vehicles = random.randint(1, 3) if customer.is_corporate else random.randint(0, 2)
            for _ in range(num_vehicles):
                vt = random.choice(vehicle_types)
                registration = f'{'LEA' if random.random() > 0.5 else 'ISL'}/{fake.random_int(min=1, max=99):02d}-{fake.random_int(min=1000, max=9999)}'
                Vehicle.objects.create(
                    customer=customer,
                    registration_number=registration,
                    vehicle_type=vt,
                    make=random.choice(['Toyota', 'Honda', 'Suzuki', 'Kia', 'Hyundai', 'Hino', 'Daewoo']),
                    model_name=fake.word().title(),
                    year=fake.random_int(min=2015, max=2025),
                    color=random.choice(['White', 'Black', 'Silver', 'Blue', 'Red', 'Grey']),
                    preferred_fuel_type=self._fuel_types[random.randint(0, 2)],
                    status='ACTIVE',
                )
                vehicle_count += 1
        self.stdout.write(f'  Created {len(self._customers)} customers, {vehicle_count} vehicles')

    def _create_purchases(self):
        self.stdout.write('Creating purchases...')
        for i in range(20):
            fuel_idx = i % len(self._fuel_types)
            tank = self._tanks[fuel_idx]
            supplier = random.choice(self._suppliers[:3])
            qty = Decimal(str(random.randint(2000, 8000)))
            price = self._fuel_types[fuel_idx].current_price * Decimal('0.85')
            Purchase.objects.create(
                purchase_number=f'PUR-{2024}-{i+1:04d}',
                supplier=supplier,
                fuel_type=self._fuel_types[fuel_idx],
                tank=tank,
                quantity=qty,
                price_per_unit=price.quantize(Decimal('0.01')),
                total_cost=(qty * price).quantize(Decimal('0.01')),
                purchase_date=fake.date_between(start_date='-60d', end_date='-1d'),
                invoice_number=f'INV-{fake.random_int(min=10000, max=99999)}',
                payment_status=random.choice(['COMPLETED', 'PENDING', 'COMPLETED', 'COMPLETED']),
                created_by=self._users[1],
            )
        self.stdout.write('  Created 20 purchases')

    def _create_inventory_items(self):
        self.stdout.write('Creating inventory items...')
        items = [
            ('Engine Oil 10W-40', 'LUB-001', 'LUBRICANT', 'Liter', 50, 10, 1200, 1500),
            ('Engine Oil 20W-50', 'LUB-002', 'LUBRICANT', 'Liter', 30, 8, 1100, 1400),
            ('Gear Oil 80W-90', 'LUB-003', 'LUBRICANT', 'Liter', 20, 5, 900, 1200),
            ('Coolant Green', 'CLT-001', 'COOLANT', 'Liter', 40, 10, 600, 800),
            ('Coolant Red', 'CLT-002', 'COOLANT', 'Liter', 15, 5, 700, 900),
            ('Brake Fluid DOT3', 'BRK-001', 'OTHER', 'Bottle', 25, 5, 400, 550),
            ('Air Filter (Car)', 'AIR-001', 'CAR_ACCESSORY', 'Piece', 60, 15, 800, 1200),
            ('Oil Filter (Car)', 'OIL-001', 'CAR_ACCESSORY', 'Piece', 80, 20, 350, 500),
            ('Windshield Wiper', 'WPR-001', 'CAR_ACCESSORY', 'Pair', 20, 5, 600, 900),
            ('Car Shampoo', 'SHM-001', 'OTHER', 'Bottle', 100, 20, 250, 400),
            ('Battery Water', 'BAT-001', 'OTHER', 'Liter', 30, 10, 100, 150),
            ('Tire Polish', 'TIR-001', 'CAR_ACCESSORY', 'Bottle', 35, 10, 450, 650),
        ]
        for name, sku, cat, unit, stock, min_stock, cost, sell in items:
            item = InventoryItem.objects.create(
                name=name, sku=sku, category=cat, unit=unit,
                current_stock=Decimal(str(stock)),
                minimum_stock_level=Decimal(str(min_stock)),
                cost_price=Decimal(str(cost)),
                selling_price=Decimal(str(sell)),
            )
            InventoryTransaction.objects.create(
                inventory_item=item,
                transaction_type='STOCK_IN',
                quantity=Decimal(str(stock)),
                previous_stock=Decimal('0'),
                new_stock=Decimal(str(stock)),
                reference='Initial stock',
                performed_by=self._users[0],
            )
        self.stdout.write('  Created 12 inventory items')

    def _create_shifts(self):
        self.stdout.write('Creating shifts...')
        today = datetime.date.today()
        self._shifts = []
        for day_offset in range(7):
            date = today - datetime.timedelta(days=day_offset)
            for pump in self._pumps:
                if pump.assigned_employee:
                    for shift_num, (start_h, end_h) in enumerate([(6, 14), (14, 22)], 1):
                        shift = Shift.objects.create(
                            employee=pump.assigned_employee,
                            pump=pump,
                            start_time=datetime.datetime.combine(date, datetime.time(start_h, 0)),
                            end_time=datetime.datetime.combine(date, datetime.time(end_h, 0)),
                            opening_cash=Decimal('5000') if shift_num == 1 else Decimal('3000'),
                            closing_cash=Decimal('15000') if day_offset > 0 else None,
                            expected_cash=Decimal('14500') if day_offset > 0 else None,
                            actual_cash=Decimal('14800') if day_offset > 0 else None,
                            cash_difference=Decimal('300') if day_offset > 0 else None,
                            total_sales=Decimal(str(random.randint(8000, 20000))) if day_offset > 0 else Decimal('0'),
                            total_transactions=random.randint(15, 50) if day_offset > 0 else 0,
                            status='CLOSED' if day_offset > 0 else 'OPEN',
                        )
                        self._shifts.append(shift)
                        for nozzle in pump.nozzles.filter(status='ACTIVE'):
                            opening = nozzle.current_meter_reading
                            fuel_dispensed = Decimal(str(random.randint(100, 800))) if day_offset > 0 else Decimal('0')
                            closing = opening + fuel_dispensed
                            nozzle.current_meter_reading = closing
                            nozzle.save(update_fields=['current_meter_reading'])
                            MeterReading.objects.create(
                                shift=shift,
                                nozzle=nozzle,
                                opening_reading=opening,
                                closing_reading=closing,
                                fuel_dispensed=fuel_dispensed,
                                sales_count=random.randint(5, 25) if day_offset > 0 else 0,
                                date=date,
                                recorded_by=pump.assigned_employee,
                            )
        self.stdout.write(f'  Created {len(self._shifts)} shifts with meter readings')

    def _create_sales(self):
        self.stdout.write('Creating sales...')
        today = datetime.date.today()
        self._sales_count = 0
        self._receipt_counter = 1
        payment_methods = ['CASH', 'CARD', 'BANK_TRANSFER', 'DIGITAL_WALLET']
        weights = [0.5, 0.25, 0.15, 0.1]
        closed_shifts = [s for s in self._shifts if s.status == 'CLOSED']

        for shift in closed_shifts:
            pump = shift.pump
            nozzles = list(pump.nozzles.filter(status='ACTIVE'))
            if not nozzles:
                continue
            num_sales = shift.total_transactions
            for _ in range(num_sales):
                nozzle = random.choice(nozzles)
                fuel_type = nozzle.fuel_type
                quantity = Decimal(str(round(random.uniform(5, 60), 2)))
                price = fuel_type.current_price
                subtotal = quantity * price
                discount = Decimal('0')
                if random.random() > 0.9:
                    discount = (subtotal * Decimal('0.02')).quantize(Decimal('0.01'))
                total = subtotal - discount
                payment_method = random.choices(payment_methods, weights=weights, k=1)[0]

                sale_time = shift.start_time + datetime.timedelta(
                    minutes=random.randint(0, int((shift.end_time - shift.start_time).total_seconds() / 60))
                )

                customer = None
                if random.random() > 0.6:
                    customer = random.choice(self._customers)

                receipt_number = f'RCP-{sale_time.strftime("%Y%m%d")}-{self._receipt_counter:06d}'
                self._receipt_counter += 1

                sale = Sale.objects.create(
                    receipt_number=receipt_number,
                    customer=customer,
                    employee=shift.employee,
                    pump=pump,
                    nozzle=nozzle,
                    fuel_type=fuel_type,
                    quantity=quantity,
                    price_per_unit=price,
                    subtotal=subtotal.quantize(Decimal('0.01')),
                    discount=discount,
                    tax_rate=Decimal('0'),
                    tax_amount=Decimal('0'),
                    total_amount=total.quantize(Decimal('0.01')),
                    payment_method=payment_method,
                    status='COMPLETED',
                    created_at=sale_time,
                )
                Payment.objects.create(
                    payment_reference=f'PAY-{sale.receipt_number}',
                    sale=sale,
                    amount=sale.total_amount,
                    payment_method=payment_method,
                    status='COMPLETED',
                    processed_by=shift.employee,
                )
                if customer and customer.is_corporate and payment_method == 'CREDIT':
                    customer.outstanding_balance += sale.total_amount
                    customer.save(update_fields=['outstanding_balance'])
                self._sales_count += 1
        self.stdout.write(f'  Created {self._sales_count} sales with payments')

    def _create_expenses(self):
        self.stdout.write('Creating expenses...')
        categories = ['ELECTRICITY', 'SALARIES', 'MAINTENANCE', 'RENT', 'SECURITY', 'CLEANING', 'EQUIPMENT', 'OTHER']
        today = datetime.date.today()
        for day_offset in range(30):
            date = today - datetime.timedelta(days=day_offset)
            num_expenses = random.randint(1, 4)
            for _ in range(num_expenses):
                category = random.choice(categories)
                if category == 'ELECTRICITY':
                    amount = Decimal(str(random.randint(15000, 40000)))
                    desc = 'Monthly electricity bill'
                elif category == 'SALARIES':
                    amount = Decimal(str(random.randint(50000, 150000)))
                    desc = f'Salary payment - {fake.name()}'
                elif category == 'RENT':
                    amount = Decimal(str(random.randint(100000, 200000)))
                    desc = 'Monthly rent payment'
                else:
                    amount = Decimal(str(random.randint(500, 20000)))
                    desc = fake.sentence()

                Expense.objects.create(
                    category=category,
                    amount=amount,
                    description=desc,
                    expense_date=date,
                    payment_method=random.choice(['CASH', 'BANK_TRANSFER', 'CARD']),
                    receipt_reference=f'RCP-{fake.random_int(min=1000, max=9999)}' if random.random() > 0.5 else '',
                    created_by=random.choice(self._users[:3]),
                )
        self.stdout.write('  Created ~90 expenses')
