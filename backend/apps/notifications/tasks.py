from celery import shared_task

from apps.fuel.models import Tank
from apps.inventory.models import InventoryItem
from apps.notifications.services import notify_low_fuel_stock, notify_low_inventory


@shared_task
def send_low_stock_alerts(fuel_type_id):
    """Check fuel stock levels and send notifications for low stock.

    In development, CELERY_TASK_ALWAYS_EAGER=True makes this run synchronously.
    """
    if fuel_type_id:
        tanks = Tank.objects.filter(
            fuel_type_id=fuel_type_id,
            status=Tank.Status.ACTIVE,
        )
    else:
        tanks = Tank.objects.filter(status=Tank.Status.ACTIVE)

    for tank in tanks:
        minimum_level = tank.fuel_type.minimum_stock_level
        if tank.current_quantity <= minimum_level:
            notify_low_fuel_stock(
                fuel_type=tank.fuel_type,
                current_stock=tank.current_quantity,
                minimum_level=minimum_level,
            )


@shared_task
def send_low_inventory_alerts():
    """Check inventory levels and send notifications for low stock items.

    In development, CELERY_TASK_ALWAYS_EAGER=True makes this run synchronously.
    """
    items = InventoryItem.objects.filter(is_active=True)

    for item in items:
        if item.current_stock <= item.minimum_stock_level:
            notify_low_inventory(
                item=item,
                current_stock=item.current_stock,
                minimum_level=item.minimum_stock_level,
            )
