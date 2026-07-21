from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import GeocodeSearchSerializer, PlanTripInputSerializer, ReverseGeocodeSerializer
from .services import RoutingError, build_trip_plan, geocode_place, geocode_suggestions, reverse_geocode


class HealthView(APIView):
	authentication_classes = []
	permission_classes = []

	def get(self, request):
		return Response({"status": "ok"}, status=status.HTTP_200_OK)


class PlanTripView(APIView):
    def post(self, request):
        serializer = PlanTripInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            plan = build_trip_plan(serializer.validated_data)
        except RoutingError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"detail": f"Unexpected planner error: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(plan, status=status.HTTP_200_OK)


class ReverseGeocodeView(APIView):
    def get(self, request):
        serializer = ReverseGeocodeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            point = reverse_geocode(
                lat=serializer.validated_data["lat"],
                lon=serializer.validated_data["lon"],
            )
        except RoutingError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"detail": f"Reverse geocode failed: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "lat": point.lat,
                "lon": point.lon,
                "label": point.label,
            },
            status=status.HTTP_200_OK,
        )


class GeocodeSearchView(APIView):
    def get(self, request):
        serializer = GeocodeSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            point = geocode_place(serializer.validated_data["q"])
        except RoutingError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"detail": f"Geocode search failed: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "lat": point.lat,
                "lon": point.lon,
                "label": point.label,
            },
            status=status.HTTP_200_OK,
        )


class GeocodeSuggestView(APIView):
	def get(self, request):
		serializer = GeocodeSearchSerializer(data=request.query_params)
		serializer.is_valid(raise_exception=True)

		try:
			points = geocode_suggestions(serializer.validated_data["q"], limit=5)
		except Exception as exc:
			return Response(
				{"detail": f"Geocode suggest failed: {exc}"},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR,
			)

		return Response(
			[
				{
					"lat": point.lat,
					"lon": point.lon,
					"label": point.label,
				}
				for point in points
			],
			status=status.HTTP_200_OK,
		)
