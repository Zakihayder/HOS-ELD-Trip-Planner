from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import asin, cos, radians, sin, sqrt
from typing import Any

import requests


HOS_DRIVING_LIMIT_HOURS = 11.0
HOS_SHIFT_WINDOW_HOURS = 14.0
HOS_BREAK_AFTER_DRIVING_HOURS = 8.0
HOS_BREAK_DURATION_HOURS = 0.5
HOS_CYCLE_LIMIT_HOURS = 70.0
HOS_REQUIRED_REST_HOURS = 10.0
HOS_RESTART_HOURS = 34.0
ASSUMED_PICKUP_HOURS = 1.0
ASSUMED_DROPOFF_HOURS = 1.0
ASSUMED_FUEL_STOP_HOURS = 0.5
ASSUMED_FUEL_EVERY_MILES = 1000.0
DEFAULT_CARRIER_NAME = "Assessment Carrier LLC"
DEFAULT_CARRIER_OFFICE = "Nashville, TN"
DEFAULT_VEHICLE_NUMBERS = "TRK-100 / TRL-200"
DEFAULT_DRIVER_SIGNATURE = "Driver Signature"
DEFAULT_CO_DRIVER = "N/A"
DEFAULT_SHIPPING_DOC = "BOL-0001"
DEFAULT_DRIVER_NUMBER = "DRV-001"
DEFAULT_DRIVER_INITIALS = "NA"
DEFAULT_HOME_TERMINAL = "Green Bay, WI"
DEFAULT_TRACTOR_NUMBER = "TRK-100"
DEFAULT_SHIPPER_NAME = "Shipper N/A"
DEFAULT_COMMODITY = "Commodity N/A"
DEFAULT_LOAD_ID = "Load-0001"

CITY_COORDINATES: dict[str, tuple[float, float]] = {
    "dallas": (32.7767, -96.7970),
    "oklahoma city": (35.4676, -97.5164),
    "nashville": (36.1627, -86.7816),
    "houston": (29.7604, -95.3698),
    "atlanta": (33.7490, -84.3880),
    "chicago": (41.8781, -87.6298),
    "los angeles": (34.0522, -118.2437),
    "new york": (40.7128, -74.0060),
    "denver": (39.7392, -104.9903),
    "phoenix": (33.4484, -112.0740),
}

STATUS_OFF_DUTY = "Off Duty"
STATUS_SLEEPER = "Sleeper Berth"
STATUS_DRIVING = "Driving"
STATUS_ON_DUTY = "On Duty (Not Driving)"


class RoutingError(Exception):
    pass


@dataclass
class GeoPoint:
    lat: float
    lon: float
    label: str


@dataclass
class PlanEvent:
    status: str
    location: str
    note: str
    start: datetime
    end: datetime

    @property
    def duration_hours(self) -> float:
        return (self.end - self.start).total_seconds() / 3600.0


class ShiftTracker:
    def __init__(self) -> None:
        self.window_remaining = HOS_SHIFT_WINDOW_HOURS
        self.driving_remaining = HOS_DRIVING_LIMIT_HOURS
        self.driving_since_break = 0.0

    def consume_driving(self, hours: float) -> None:
        self.window_remaining -= hours
        self.driving_remaining -= hours
        self.driving_since_break += hours

    def consume_non_driving(self, hours: float) -> None:
        self.window_remaining -= hours

    def reset(self) -> None:
        self.window_remaining = HOS_SHIFT_WINDOW_HOURS
        self.driving_remaining = HOS_DRIVING_LIMIT_HOURS
        self.driving_since_break = 0.0


def geocode_place(query: str) -> GeoPoint:
    url = "https://nominatim.openstreetmap.org/search"
    try:
        response = requests.get(
            url,
            params={"q": query, "format": "json", "limit": 1, "accept-language": "en"},
            headers={"User-Agent": "hos-planner-assessment-app/1.0", "Accept-Language": "en"},
            timeout=20,
        )
        response.raise_for_status()
        items = response.json()
        if items:
            first = items[0]
            return GeoPoint(
                lat=float(first["lat"]),
                lon=float(first["lon"]),
                label=first.get("display_name", query),
            )
    except requests.RequestException:
        pass

    fallback = fallback_geocode(query)
    if fallback is None:
        raise RoutingError(
            f"Could not geocode location: {query}. Internet lookup failed and no local fallback match was found."
        )
    return fallback


def geocode_suggestions(query: str, limit: int = 5) -> list[GeoPoint]:
    if not query.strip():
        return []

    url = "https://nominatim.openstreetmap.org/search"
    try:
        response = requests.get(
            url,
            params={"q": query, "format": "json", "limit": limit, "accept-language": "en"},
            headers={"User-Agent": "hos-planner-assessment-app/1.0", "Accept-Language": "en"},
            timeout=20,
        )
        response.raise_for_status()
        items = response.json()
        if items:
            return [
                GeoPoint(
                    lat=float(item["lat"]),
                    lon=float(item["lon"]),
                    label=item.get("display_name", query),
                )
                for item in items[:limit]
            ]
    except requests.RequestException:
        pass

    query_lower = query.lower().strip()
    fallback_matches: list[GeoPoint] = []
    for city, (lat, lon) in CITY_COORDINATES.items():
        if query_lower in city:
            fallback_matches.append(GeoPoint(lat=lat, lon=lon, label=city.title()))
    return fallback_matches[:limit]


def reverse_geocode(lat: float, lon: float) -> GeoPoint:
    url = "https://nominatim.openstreetmap.org/reverse"
    try:
        response = requests.get(
            url,
            params={"lat": lat, "lon": lon, "format": "jsonv2", "accept-language": "en"},
            headers={"User-Agent": "hos-planner-assessment-app/1.0", "Accept-Language": "en"},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        label = payload.get("display_name")
        if label:
            return GeoPoint(lat=lat, lon=lon, label=label)
    except requests.RequestException:
        pass

    return GeoPoint(lat=lat, lon=lon, label=f"Lat {lat:.5f}, Lon {lon:.5f}")


def build_route(points: list[GeoPoint]) -> dict[str, Any]:
    coords = ";".join(f"{p.lon},{p.lat}" for p in points)
    url = f"https://router.project-osrm.org/route/v1/driving/{coords}"
    try:
        response = requests.get(
            url,
            params={"overview": "full", "geometries": "geojson", "steps": "true"},
            timeout=20,
        )
        response.raise_for_status()

        payload = response.json()
        routes = payload.get("routes", [])
        if routes:
            route = routes[0]
            legs = route.get("legs", [])
            steps: list[dict[str, Any]] = []
            for leg in legs:
                for step in leg.get("steps", []):
                    maneuver = step.get("maneuver", {})
                    steps.append(
                        {
                            "instruction": maneuver.get("instruction") or maneuver.get("type", "Continue"),
                            "distance_miles": meters_to_miles(step.get("distance", 0.0)),
                            "duration_minutes": round(step.get("duration", 0.0) / 60.0, 1),
                        }
                    )

            return {
                "distance_miles": meters_to_miles(route.get("distance", 0.0)),
                "duration_hours": route.get("duration", 0.0) / 3600.0,
                "geometry": route.get("geometry", {}),
                "steps": steps,
            }
    except requests.RequestException:
        pass

    # Offline fallback: straight-line route estimation with simple steps.
    total_miles = 0.0
    line_coordinates: list[list[float]] = []
    fallback_steps: list[dict[str, Any]] = []
    for index, point in enumerate(points):
        line_coordinates.append([point.lon, point.lat])
        if index == 0:
            continue
        prev = points[index - 1]
        leg_miles = haversine_miles(prev.lat, prev.lon, point.lat, point.lon)
        total_miles += leg_miles
        fallback_steps.append(
            {
                "instruction": f"Drive from {prev.label} to {point.label}",
                "distance_miles": round(leg_miles, 2),
                "duration_minutes": round((leg_miles / 50.0) * 60.0, 1),
            }
        )

    return {
        "distance_miles": round(total_miles, 2),
        "duration_hours": round(total_miles / 50.0, 2),
        "geometry": {"type": "LineString", "coordinates": line_coordinates},
        "steps": fallback_steps,
    }


def fallback_geocode(query: str) -> GeoPoint | None:
    parsed = parse_coordinate_string(query)
    if parsed is not None:
        lat, lon = parsed
        return GeoPoint(lat=lat, lon=lon, label=f"Lat {lat:.5f}, Lon {lon:.5f}")

    query_lower = query.lower().strip()
    for city, (lat, lon) in CITY_COORDINATES.items():
        if city in query_lower:
            return GeoPoint(lat=lat, lon=lon, label=query)
    return None


def parse_coordinate_string(text: str) -> tuple[float, float] | None:
    parts = [part.strip() for part in text.split(",")]
    if len(parts) != 2:
        return None

    try:
        lat = float(parts[0])
        lon = float(parts[1])
    except ValueError:
        return None

    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return lat, lon
    return None


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_miles = 3958.7613
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return radius_miles * c


def meters_to_miles(meters: float) -> float:
    return round(meters * 0.000621371, 2)


def add_event(events: list[PlanEvent], status: str, hours: float, location: str, note: str, current_time: datetime) -> datetime:
    if hours <= 0:
        return current_time
    event = PlanEvent(
        status=status,
        location=location,
        note=note,
        start=current_time,
        end=current_time + timedelta(hours=hours),
    )
    events.append(event)
    return event.end


def enforce_shift_and_cycle(events: list[PlanEvent], current_time: datetime, shift: ShiftTracker, remaining_cycle: float) -> tuple[datetime, float]:
    if remaining_cycle <= 0.0:
        current_time = add_event(
            events,
            STATUS_OFF_DUTY,
            HOS_RESTART_HOURS,
            "Rest Area",
            "34-hour restart to refresh 70/8 cycle",
            current_time,
        )
        remaining_cycle = HOS_CYCLE_LIMIT_HOURS
        shift.reset()

    if shift.window_remaining <= 0.0 or shift.driving_remaining <= 0.0:
        current_time = add_event(
            events,
            STATUS_OFF_DUTY,
            HOS_REQUIRED_REST_HOURS,
            "Rest Area",
            "10-hour off-duty reset",
            current_time,
        )
        shift.reset()

    return current_time, remaining_cycle


def plan_trip_schedule(
    *,
    start_point: GeoPoint,
    pickup_point: GeoPoint,
    dropoff_point: GeoPoint,
    current_cycle_used_hours: float,
    route: dict[str, Any],
    start_time: datetime | None = None,
    log_meta: dict[str, str] | None = None,
) -> dict[str, Any]:
    if current_cycle_used_hours < 0 or current_cycle_used_hours > HOS_CYCLE_LIMIT_HOURS:
        raise RoutingError("Current cycle used hours must be between 0 and 70.")

    if start_time is None:
        current_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    else:
        current_time = start_time
    shift = ShiftTracker()
    remaining_cycle = HOS_CYCLE_LIMIT_HOURS - current_cycle_used_hours
    if remaining_cycle < 0:
        remaining_cycle = 0.0

    route_hours_remaining = float(route["duration_hours"])
    route_miles = float(route["distance_miles"])
    avg_speed = route_miles / route_hours_remaining if route_hours_remaining > 0 else 55.0
    avg_speed = max(20.0, min(avg_speed, 70.0))

    events: list[PlanEvent] = []
    fuel_miles_since_last_stop = 0.0

    # Pre-trip pickup is on-duty not driving and consumes shift window and cycle.
    pickup_hours = min(ASSUMED_PICKUP_HOURS, max(shift.window_remaining, 0.0), max(remaining_cycle, 0.0))
    if pickup_hours <= 0:
        current_time, remaining_cycle = enforce_shift_and_cycle(events, current_time, shift, remaining_cycle)
        pickup_hours = min(ASSUMED_PICKUP_HOURS, shift.window_remaining, remaining_cycle)
    current_time = add_event(events, STATUS_ON_DUTY, pickup_hours, pickup_point.label, "Pickup time", current_time)
    shift.consume_non_driving(pickup_hours)
    remaining_cycle -= pickup_hours

    while route_hours_remaining > 0.0001:
        current_time, remaining_cycle = enforce_shift_and_cycle(events, current_time, shift, remaining_cycle)

        if shift.driving_since_break >= HOS_BREAK_AFTER_DRIVING_HOURS:
            break_hours = min(HOS_BREAK_DURATION_HOURS, shift.window_remaining, remaining_cycle)
            if break_hours <= 0:
                current_time, remaining_cycle = enforce_shift_and_cycle(events, current_time, shift, 0.0)
                continue
            current_time = add_event(events, STATUS_ON_DUTY, break_hours, "Roadside", "30-minute break", current_time)
            shift.consume_non_driving(break_hours)
            remaining_cycle -= break_hours
            shift.driving_since_break = 0.0
            continue

        max_until_break = HOS_BREAK_AFTER_DRIVING_HOURS - shift.driving_since_break
        drive_segment = min(
            route_hours_remaining,
            shift.driving_remaining,
            shift.window_remaining,
            remaining_cycle,
            max_until_break,
        )

        if drive_segment <= 0.0:
            current_time, remaining_cycle = enforce_shift_and_cycle(events, current_time, shift, remaining_cycle)
            if drive_segment <= 0.0 and (shift.window_remaining <= 0.0 or shift.driving_remaining <= 0.0):
                continue
            if remaining_cycle <= 0.0:
                continue
            raise RoutingError("Unable to schedule remaining driving hours within current constraints.")

        current_time = add_event(events, STATUS_DRIVING, drive_segment, "In Transit", "En route", current_time)
        shift.consume_driving(drive_segment)
        remaining_cycle -= drive_segment
        route_hours_remaining -= drive_segment

        segment_miles = drive_segment * avg_speed
        fuel_miles_since_last_stop += segment_miles

        if fuel_miles_since_last_stop >= ASSUMED_FUEL_EVERY_MILES and route_hours_remaining > 0.0001:
            fuel_stop_hours = min(ASSUMED_FUEL_STOP_HOURS, shift.window_remaining, remaining_cycle)
            if fuel_stop_hours > 0:
                current_time = add_event(events, STATUS_ON_DUTY, fuel_stop_hours, "Fuel Stop", "Fueling stop", current_time)
                shift.consume_non_driving(fuel_stop_hours)
                remaining_cycle -= fuel_stop_hours
                fuel_miles_since_last_stop = 0.0

    # Drop-off may require starting a new shift if the current one is exhausted.
    drop_hours_left = ASSUMED_DROPOFF_HOURS
    while drop_hours_left > 0.0001:
        current_time, remaining_cycle = enforce_shift_and_cycle(events, current_time, shift, remaining_cycle)
        chunk = min(drop_hours_left, shift.window_remaining, remaining_cycle)
        if chunk <= 0.0:
            current_time, remaining_cycle = enforce_shift_and_cycle(events, current_time, shift, 0.0)
            continue
        current_time = add_event(events, STATUS_ON_DUTY, chunk, dropoff_point.label, "Drop-off time", current_time)
        shift.consume_non_driving(chunk)
        remaining_cycle -= chunk
        drop_hours_left -= chunk

    events_payload = [
        {
            "status": event.status,
            "location": event.location,
            "note": event.note,
            "start": event.start.isoformat(),
            "end": event.end.isoformat(),
            "duration_hours": round(event.duration_hours, 2),
        }
        for event in events
    ]

    daily_logs = build_fmcsa_daily_logs(events, avg_speed, log_meta or {})

    compliance = {
        "rule_set": "Property-carrying 70hrs/8days",
        "driving_limit_hours": HOS_DRIVING_LIMIT_HOURS,
        "shift_window_hours": HOS_SHIFT_WINDOW_HOURS,
        "break_after_driving_hours": HOS_BREAK_AFTER_DRIVING_HOURS,
        "cycle_limit_hours": HOS_CYCLE_LIMIT_HOURS,
        "current_cycle_used_hours": current_cycle_used_hours,
        "estimated_days": len(daily_logs),
        "remaining_cycle_hours_after_trip": round(remaining_cycle, 2),
    }

    return {
        "assumptions": {
            "no_adverse_conditions": True,
            "fuel_every_miles": ASSUMED_FUEL_EVERY_MILES,
            "pickup_hours": ASSUMED_PICKUP_HOURS,
            "dropoff_hours": ASSUMED_DROPOFF_HOURS,
        },
        "route": route,
        "events": events_payload,
        "compliance": compliance,
        "daily_logs": daily_logs,
        "locations": {
            "current": start_point.__dict__,
            "pickup": pickup_point.__dict__,
            "dropoff": dropoff_point.__dict__,
        },
    }


def build_fmcsa_daily_logs(events: list[PlanEvent], avg_speed: float, log_meta: dict[str, str]) -> list[dict[str, Any]]:
    if not events:
        return []

    first_day = events[0].start.date()
    last_day = events[-1].end.date()
    total_days = (last_day - first_day).days + 1

    logs: list[dict[str, Any]] = []
    for day_offset in range(total_days):
        day_date = first_day + timedelta(days=day_offset)
        day_start = datetime(day_date.year, day_date.month, day_date.day, tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)

        day_segments: list[dict[str, Any]] = []
        remarks: list[str] = []

        for event in events:
            overlap_start = max(event.start, day_start)
            overlap_end = min(event.end, day_end)
            if overlap_end <= overlap_start:
                continue

            overlap_hours = (overlap_end - overlap_start).total_seconds() / 3600.0
            start_hour = (overlap_start - day_start).total_seconds() / 3600.0
            end_hour = (overlap_end - day_start).total_seconds() / 3600.0

            day_segments.append(
                {
                    "status": event.status,
                    "start_hour": round(start_hour, 4),
                    "end_hour": round(end_hour, 4),
                    "location": event.location,
                    "note": event.note,
                }
            )

            if day_start <= event.start < day_end:
                remarks.append(
                    f"{event.start.strftime('%H:%M')} {event.location} - {event.status} ({event.note})"
                )

        graph_segments: list[dict[str, Any]] = []
        cursor = 0.0
        for segment in sorted(day_segments, key=lambda seg: seg["start_hour"]):
            start_hour = float(segment["start_hour"])
            end_hour = float(segment["end_hour"])
            if start_hour > cursor:
                graph_segments.append(
                    {
                        "status": STATUS_OFF_DUTY,
                        "start_hour": round(cursor, 4),
                        "end_hour": round(start_hour, 4),
                        "location": "Off Duty",
                        "note": "Auto-filled to complete 24-hour record",
                    }
                )
            graph_segments.append(segment)
            cursor = max(cursor, end_hour)

        if cursor < 24.0:
            graph_segments.append(
                {
                    "status": STATUS_OFF_DUTY,
                    "start_hour": round(cursor, 4),
                    "end_hour": 24.0,
                    "location": "Off Duty",
                    "note": "Auto-filled to complete 24-hour record",
                }
            )

        driving_hours = 0.0
        sleeper_hours = 0.0
        on_duty_not_driving_hours = 0.0
        off_duty_hours = 0.0
        for segment in graph_segments:
            span = float(segment["end_hour"]) - float(segment["start_hour"])
            if segment["status"] == STATUS_DRIVING:
                driving_hours += span
            elif segment["status"] == STATUS_SLEEPER:
                sleeper_hours += span
            elif segment["status"] == STATUS_ON_DUTY:
                on_duty_not_driving_hours += span
            else:
                off_duty_hours += span

        on_duty_plus_driving = on_duty_not_driving_hours + driving_hours
        total_miles = round(driving_hours * avg_speed, 2)

        logs.append(
            {
                "date": day_date.isoformat(),
                "total_miles_driving_today": total_miles,
                "total_truck_miles_today": total_miles,
                "carrier_name": DEFAULT_CARRIER_NAME,
                "main_office_address": DEFAULT_CARRIER_OFFICE,
                "vehicle_numbers": log_meta.get("vehicle_numbers") or DEFAULT_VEHICLE_NUMBERS,
                "driver_signature": log_meta.get("driver_signature") or DEFAULT_DRIVER_SIGNATURE,
                "driver_number": log_meta.get("driver_number") or DEFAULT_DRIVER_NUMBER,
                "driver_initials": log_meta.get("driver_initials") or DEFAULT_DRIVER_INITIALS,
                "co_driver_name": log_meta.get("co_driver_name") or DEFAULT_CO_DRIVER,
                "home_terminal": log_meta.get("home_terminal") or DEFAULT_HOME_TERMINAL,
                "tractor_number": log_meta.get("tractor_number") or DEFAULT_TRACTOR_NUMBER,
                "trailer_numbers": log_meta.get("trailer_numbers") or DEFAULT_VEHICLE_NUMBERS,
                "shipper_name": log_meta.get("shipper_name") or DEFAULT_SHIPPER_NAME,
                "commodity": log_meta.get("commodity") or DEFAULT_COMMODITY,
                "load_id": log_meta.get("load_id") or DEFAULT_LOAD_ID,
                "shipping_document": log_meta.get("load_id") or DEFAULT_SHIPPING_DOC,
                "time_base": "UTC",
                "remarks": remarks,
                "graph_segments": sorted(graph_segments, key=lambda seg: seg["start_hour"]),
                "totals": {
                    STATUS_OFF_DUTY: round(off_duty_hours, 2),
                    STATUS_SLEEPER: round(sleeper_hours, 2),
                    STATUS_DRIVING: round(driving_hours, 2),
                    STATUS_ON_DUTY: round(on_duty_not_driving_hours, 2),
                    "all_status_total": round(off_duty_hours + sleeper_hours + driving_hours + on_duty_not_driving_hours, 2),
                    "off_duty_hhmm": hours_to_hhmm(off_duty_hours),
                    "sleeper_hhmm": hours_to_hhmm(sleeper_hours),
                    "driving_hhmm": hours_to_hhmm(driving_hours),
                    "on_duty_hhmm": hours_to_hhmm(on_duty_not_driving_hours),
                    "on_duty_plus_driving_hours_decimal": round(on_duty_plus_driving, 2),
                    "on_duty_plus_driving_hhmm": hours_to_hhmm(on_duty_plus_driving),
                },
            }
        )

    return logs


def build_trip_plan(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("current_lat") is not None and payload.get("current_lon") is not None:
        current = reverse_geocode(float(payload["current_lat"]), float(payload["current_lon"]))
    else:
        current = geocode_place(payload["current_location"])

    if payload.get("pickup_lat") is not None and payload.get("pickup_lon") is not None:
        pickup = reverse_geocode(float(payload["pickup_lat"]), float(payload["pickup_lon"]))
    else:
        pickup = geocode_place(payload["pickup_location"])

    if payload.get("dropoff_lat") is not None and payload.get("dropoff_lon") is not None:
        dropoff = reverse_geocode(float(payload["dropoff_lat"]), float(payload["dropoff_lon"]))
    else:
        dropoff = geocode_place(payload["dropoff_location"])

    route = build_route([current, pickup, dropoff])
    log_meta = {
        "driver_number": str(payload.get("driver_number") or "").strip(),
        "driver_initials": str(payload.get("driver_initials") or "").strip(),
        "driver_signature": str(payload.get("driver_signature") or "").strip(),
        "co_driver_name": str(payload.get("co_driver_name") or "").strip(),
        "home_terminal": str(payload.get("home_terminal") or "").strip(),
        "tractor_number": str(payload.get("tractor_number") or "").strip(),
        "trailer_numbers": str(payload.get("trailer_numbers") or "").strip(),
        "shipper_name": str(payload.get("shipper_name") or "").strip(),
        "commodity": str(payload.get("commodity") or "").strip(),
        "load_id": str(payload.get("load_id") or "").strip(),
        "vehicle_numbers": " / ".join(
            [
                value
                for value in [
                    str(payload.get("tractor_number") or "").strip(),
                    str(payload.get("trailer_numbers") or "").strip(),
                ]
                if value
            ]
        )
        or DEFAULT_VEHICLE_NUMBERS,
    }

    return plan_trip_schedule(
        start_point=current,
        pickup_point=pickup,
        dropoff_point=dropoff,
        current_cycle_used_hours=float(payload["current_cycle_used_hours"]),
        route=route,
        log_meta=log_meta,
    )


def hours_to_hhmm(hours: float) -> str:
    total_minutes = int(round(hours * 60))
    hh = total_minutes // 60
    mm = total_minutes % 60
    return f"{hh:02d}:{mm:02d}"
