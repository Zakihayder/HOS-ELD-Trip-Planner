from django.urls import path

from .views import GeocodeSearchView, GeocodeSuggestView, HealthView, PlanTripView, ReverseGeocodeView

urlpatterns = [
    path('health', HealthView.as_view(), name='health'),
    path('plan-trip', PlanTripView.as_view(), name='plan-trip'),
    path('reverse-geocode', ReverseGeocodeView.as_view(), name='reverse-geocode'),
    path('geocode', GeocodeSearchView.as_view(), name='geocode-search'),
    path('geocode-suggest', GeocodeSuggestView.as_view(), name='geocode-suggest'),
]
