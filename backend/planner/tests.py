from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from datetime import datetime, timezone

from planner.services import (
    STATUS_DRIVING,
    STATUS_OFF_DUTY,
    STATUS_ON_DUTY,
    plan_trip_schedule,
)


class PlanTripApiTests(APITestCase):
    def test_health_endpoint(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")

    def test_rejects_invalid_payload(self):
        response = self.client.post(reverse("plan-trip"), data={}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("current_location", response.data)

    @patch("planner.views.build_trip_plan")
    def test_returns_trip_plan_for_valid_payload(self, mock_build_trip_plan):
        mock_build_trip_plan.return_value = {
            "route": {"distance_miles": 100.0, "duration_hours": 2.0, "steps": []},
            "events": [],
            "compliance": {"estimated_days": 1},
            "daily_logs": [],
            "locations": {},
            "assumptions": {},
        }

        payload = {
            "current_location": "Dallas, TX",
            "pickup_location": "Oklahoma City, OK",
            "dropoff_location": "Nashville, TN",
            "current_cycle_used_hours": 20,
        }

        response = self.client.post(reverse("plan-trip"), data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("route", response.data)
        self.assertIn("daily_logs", response.data)

    @patch("planner.views.reverse_geocode")
    def test_reverse_geocode_endpoint_returns_location(self, mock_reverse_geocode):
        mock_reverse_geocode.return_value = type(
            "Point",
            (),
            {"lat": 32.7767, "lon": -96.7970, "label": "Dallas, TX"},
        )()

        response = self.client.get(reverse("reverse-geocode"), data={"lat": 32.7767, "lon": -96.7970})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["label"], "Dallas, TX")

    @patch("planner.views.geocode_place")
    def test_geocode_search_endpoint_returns_location(self, mock_geocode_place):
        mock_geocode_place.return_value = type(
            "Point",
            (),
            {"lat": 35.4676, "lon": -97.5164, "label": "Oklahoma City, OK"},
        )()

        response = self.client.get(reverse("geocode-search"), data={"q": "Oklahoma City"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["label"], "Oklahoma City, OK")

    @patch("planner.views.geocode_suggestions")
    def test_geocode_suggest_endpoint_returns_list(self, mock_geocode_suggestions):
        mock_geocode_suggestions.return_value = [
            type("Point", (), {"lat": 35.4676, "lon": -97.5164, "label": "Oklahoma City, OK"})(),
            type("Point", (), {"lat": 35.2226, "lon": -97.4395, "label": "Norman, OK"})(),
        ]

        response = self.client.get(reverse("geocode-suggest"), data={"q": "okla"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class HosPlannerRuleTests(APITestCase):
    def _build_plan(
        self,
        duration_hours: float,
        current_cycle_used_hours: float = 10.0,
        start_time: datetime | None = None,
    ):
        route = {
            "distance_miles": duration_hours * 55.0,
            "duration_hours": duration_hours,
            "geometry": {"coordinates": []},
            "steps": [],
        }
        start_point = type("P", (), {"lat": 32.77, "lon": -96.79, "label": "Dallas"})()
        pickup_point = type("P", (), {"lat": 35.46, "lon": -97.51, "label": "Oklahoma City"})()
        dropoff_point = type("P", (), {"lat": 36.16, "lon": -86.78, "label": "Nashville"})()

        return plan_trip_schedule(
            start_point=start_point,
            pickup_point=pickup_point,
            dropoff_point=dropoff_point,
            current_cycle_used_hours=current_cycle_used_hours,
            route=route,
            start_time=start_time,
        )

    def test_inserts_30_minute_break_after_8_hours_driving(self):
        plan = self._build_plan(duration_hours=9.0)
        events = plan["events"]

        break_events = [
            event for event in events if event["status"] == STATUS_ON_DUTY and "30-minute break" in event["note"]
        ]
        self.assertGreaterEqual(len(break_events), 1)

    def test_respects_11_hour_driving_cap_per_shift(self):
        plan = self._build_plan(duration_hours=13.0)
        events = plan["events"]

        driving_events = [event for event in events if event["status"] == STATUS_DRIVING]
        self.assertTrue(driving_events)

        # No single driving segment may exceed 11 hours.
        self.assertTrue(all(event["duration_hours"] <= 11.0 for event in driving_events))

        off_duty_resets = [event for event in events if event["status"] == STATUS_OFF_DUTY and "10-hour" in event["note"]]
        self.assertGreaterEqual(len(off_duty_resets), 1)

    def test_respects_14_hour_shift_window(self):
        plan = self._build_plan(duration_hours=16.0)
        events = plan["events"]

        shift_on_duty = 0.0
        for event in events:
            status_name = event["status"]
            duration = float(event["duration_hours"])
            if status_name in {STATUS_DRIVING, STATUS_ON_DUTY}:
                shift_on_duty += duration
            if status_name == STATUS_OFF_DUTY and "10-hour off-duty reset" in event["note"]:
                self.assertLessEqual(shift_on_duty, 14.0)
                shift_on_duty = 0.0

    def test_inserts_restart_when_cycle_limit_exhausted(self):
        plan = self._build_plan(duration_hours=3.0, current_cycle_used_hours=69.0)
        events = plan["events"]

        restart_events = [
            event
            for event in events
            if event["status"] == STATUS_OFF_DUTY and "34-hour restart" in event["note"]
        ]
        self.assertGreaterEqual(len(restart_events), 1)

    def test_daily_logs_total_24_hours(self):
        plan = self._build_plan(duration_hours=12.5)

        for log in plan["daily_logs"]:
            self.assertAlmostEqual(log["totals"]["all_status_total"], 24.0, places=2)
            self.assertIn("driver_number", log)
            self.assertIn("driver_initials", log)
            self.assertIn("home_terminal", log)
            self.assertIn("tractor_number", log)
            self.assertIn("trailer_numbers", log)
            self.assertIn("shipper_name", log)
            self.assertIn("commodity", log)
            self.assertIn("load_id", log)
            self.assertRegex(log["totals"]["driving_hhmm"], r"^\d{2}:\d{2}$")
            self.assertRegex(log["totals"]["on_duty_hhmm"], r"^\d{2}:\d{2}$")

    def test_midnight_split_creates_multiple_log_days(self):
        start_time = datetime(2026, 7, 21, 23, 0, tzinfo=timezone.utc)
        plan = self._build_plan(duration_hours=4.0, start_time=start_time)
        self.assertGreaterEqual(len(plan["daily_logs"]), 2)

    def test_long_haul_generates_multi_day_logs(self):
        plan = self._build_plan(duration_hours=30.0, current_cycle_used_hours=5.0)
        self.assertGreaterEqual(len(plan["daily_logs"]), 3)
