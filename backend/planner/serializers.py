from rest_framework import serializers


class PlanTripInputSerializer(serializers.Serializer):
    current_location = serializers.CharField(max_length=255)
    pickup_location = serializers.CharField(max_length=255)
    dropoff_location = serializers.CharField(max_length=255)
    current_cycle_used_hours = serializers.FloatField(min_value=0.0, max_value=70.0)
    current_lat = serializers.FloatField(required=False)
    current_lon = serializers.FloatField(required=False)
    pickup_lat = serializers.FloatField(required=False)
    pickup_lon = serializers.FloatField(required=False)
    dropoff_lat = serializers.FloatField(required=False)
    dropoff_lon = serializers.FloatField(required=False)
    driver_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    driver_initials = serializers.CharField(max_length=20, required=False, allow_blank=True)
    driver_signature = serializers.CharField(max_length=255, required=False, allow_blank=True)
    co_driver_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    home_terminal = serializers.CharField(max_length=255, required=False, allow_blank=True)
    tractor_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    trailer_numbers = serializers.CharField(max_length=255, required=False, allow_blank=True)
    shipper_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    commodity = serializers.CharField(max_length=255, required=False, allow_blank=True)
    load_id = serializers.CharField(max_length=255, required=False, allow_blank=True)


class ReverseGeocodeSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lon = serializers.FloatField()


class GeocodeSearchSerializer(serializers.Serializer):
    q = serializers.CharField(max_length=255)
