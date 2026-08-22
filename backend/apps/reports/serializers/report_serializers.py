from rest_framework import serializers


class DailySalesBreakdownSerializer(serializers.Serializer):
    date = serializers.CharField()
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    liters = serializers.DecimalField(max_digits=14, decimal_places=2)
    transactions = serializers.IntegerField()


class FuelTypeBreakdownSerializer(serializers.Serializer):
    fuel_type = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=14, decimal_places=2)
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)


class DailyExpenseSerializer(serializers.Serializer):
    date = serializers.CharField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)


class ExpenseByCategorySerializer(serializers.Serializer):
    category = serializers.CharField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
