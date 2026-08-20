from django.db import models


class PumpFuelType(models.Model):
    """Through model for Pump-FuelType many-to-many relationship."""

    id = models.BigAutoField(primary_key=True)
    pump = models.ForeignKey(
        'pumps.Pump',
        on_delete=models.CASCADE,
        related_name='pump_fuel_types',
    )
    fuel_type = models.ForeignKey(
        'fuel.FuelType',
        on_delete=models.CASCADE,
        related_name='pump_fuel_types',
    )

    class Meta:
        db_table = 'pump_fuel_types'
        verbose_name = 'Pump Fuel Type'
        verbose_name_plural = 'Pump Fuel Types'
        unique_together = ('pump', 'fuel_type')

    def __str__(self):
        return f'{self.pump.pump_number} - {self.fuel_type.name}'
