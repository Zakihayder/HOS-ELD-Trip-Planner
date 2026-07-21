# Full Stack Assessment Execution Guide

## 1) What the Assignment Requires (from provided materials)

### Required stack
- Backend: Django
- Frontend: React

### Required deliverables
- Live hosted app (assessment notes mention Vercel as an example)
- 3-5 minute Loom walkthrough (product + code)
- Public GitHub repository

### Product objective
Build an app that accepts:
- Current location
- Pickup location
- Dropoff location
- Current cycle used (hours)

And outputs:
- Route instructions on a map with stops/rests
- Completed ELD-style daily log sheets (multiple days for long trips)

### Assumptions to enforce
- Property-carrying driver
- 70 hours / 8 days cycle
- No adverse driving conditions
- Fuel stop at least every 1000 miles
- 1 hour for pickup and 1 hour for drop-off

### Compliance-critical HOS logic from FMCSA guide
- 11-hour driving limit (within shift)
- 14-hour driving window (after coming on duty)
- 30-minute break required after 8 cumulative driving hours
- 70-hour / 8-day rolling on-duty limit
- Optional 34-hour restart concept exists, but only include if explicitly modeled
- Daily log requires 24-hour grid and required metadata fields

## 2) Build Strategy (to maximize success probability)

### Phase A: Deliver a correct planning engine first
Implement a deterministic trip planner service that:
1. Consumes route distance/time from a map API.
2. Builds a timeline of duty-status segments:
   - Off Duty
   - Sleeper Berth (optional; can be skipped in first version)
   - Driving
   - On Duty (Not Driving)
3. Inserts required events:
   - Pickup (1h on-duty not driving)
   - Drop-off (1h on-duty not driving)
   - Fuel stop every <= 1000 miles (on-duty not driving, configurable duration)
   - 30-minute break whenever cumulative driving reaches 8h
4. Enforces legal limits:
   - No driving past 11h total driving in shift
   - No driving past 14h from shift start
   - No driving if rolling 8-day on-duty total would exceed 70h
5. Splits output into day-by-day logs.

### Phase B: Render logs exactly as assessors expect
- Draw the 24-hour log grid with four duty rows.
- Plot horizontal/vertical line transitions by timestamp.
- Fill required page fields:
  - Date
  - Total miles driving today
  - Vehicle/unit identifiers
  - Carrier name and main office address
  - Driver signature placeholder
  - Co-driver (if none, show N/A)
  - Remarks (location at each duty-status change)
  - Shipping document / shipper and commodity placeholder
  - Totals for each duty status summing to 24h

### Phase C: Polish UX/UI
- Clear, modern layout with:
  - Left: Input form + assumptions summary
  - Right: Route map + stop cards + compliance summary
  - Secondary tab/panel: Daily logs viewer (Day 1, Day 2, ...)
- Add strong visual clarity around:
  - Remaining driving hours
  - Remaining 14-hour window
  - Remaining 70-hour cycle

## 3) Recommended Architecture

### Frontend (React)
- Pages/components:
  - TripForm
  - RouteMap
  - ComplianceSummary
  - TimelineView
  - DailyLogSheetRenderer
- State:
  - Single source of truth for trip input + computed plan
- API integration:
  - POST /api/plan-trip

### Backend (Django + DRF)
- Endpoint:
  - POST /api/plan-trip
- Services:
  - RouteService (map API wrapper)
  - HosPlannerService (rule engine)
  - LogSheetService (daily split + render payload)
- Validation:
  - Input schema validation
  - Rule sanity checks

### Data contract (minimal)
Input:
- current_location
- pickup_location
- dropoff_location
- current_cycle_used_hours

Output:
- route: polyline/legs/steps
- events: ordered timeline segments
- compliance: rule counters and flags
- log_sheets: array of per-day grid + metadata payload

## 4) Implementation Order (fastest path to functional demo)

1. Scaffold Django API + React app.
2. Integrate one free map API and return route distance + duration.
3. Implement core HOS planner without visualization.
4. Write unit tests for planner edge cases.
5. Build map + event list UI.
6. Build ELD log sheet renderer.
7. Add validations/error handling.
8. Deploy frontend + backend.
9. Record Loom and finalize README.

## 5) Acceptance Criteria (definition of done)

A submission is ready when all are true:
- App is publicly reachable and stable.
- Inputs work for multiple trip distances.
- Output includes route + stops + legally constrained schedule.
- Multi-day log sheets generate when trip exceeds one day.
- 30-minute break and 11/14/70 logic are visible and enforced.
- UI is clean and understandable.
- GitHub repo includes setup and architecture notes.
- Loom explains product flow, rules, and code.

## 6) Risk Register + Mitigations

### Risk: HOS logic bugs
Mitigation:
- Table-driven tests for each rule boundary (7.9h/8h break, 10.9h/11h driving, 13.9h/14h window, 69.9h/70h cycle).

### Risk: Log rendering inaccuracies
Mitigation:
- Generate grid from normalized 24h segments.
- Add visual test fixtures for known scenarios.

### Risk: Deployment complexity
Mitigation:
- Keep backend stateless.
- Use environment variables for API keys.
- Verify CORS and HTTPS before final recording.

## 7) 100% Status Check (current)

Current completion: FUNCTIONALLY COMPLETE in local environment.

What is complete now:
- Django + React full-stack implementation.
- HOS planning engine with boundary tests.
- FMCSA daily log graph rendering.
- Real map interaction (search, suggest, drag/pan, click pick).
- Backend health endpoint and frontend health indicator.
- Print/PDF and JSON export options for log outputs.
- Offline fallback behavior for map/geocode outages.

What remains for final submission close-out:
- Deploy frontend and backend publicly.
- Record Loom walkthrough.
- Share final links (live app + GitHub + Loom).

## 8) Practical Timeline

- Day 1: Project scaffold + map API + basic endpoint
- Day 2: HOS planner + tests
- Day 3: Log sheet renderer + UX polish
- Day 4: Deployment + bug fixes + Loom + final submission

If executed with discipline, this is realistically completable in 3-4 focused days.
