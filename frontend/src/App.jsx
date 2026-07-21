import { useEffect, useMemo, useRef, useState } from "react";

import { planTrip, reverseGeocode } from "./api";
import Card3D from "./components/Card3D";
import ChipToggle from "./components/ChipToggle";
import DailyLogTable from "./components/DailyLogTable";
import HeroIllustration from "./components/HeroIllustration";
import LocationSelectorMap from "./components/LocationSelectorMap";
import RouteMap from "./components/RouteMap";
import "./index.css";

const initialForm = {
  current_location: "Dallas, TX",
  pickup_location: "Oklahoma City, OK",
  dropoff_location: "Nashville, TN",
  current_cycle_used_hours: 24,
  driver_number: "DRV-001",
  driver_initials: "NA",
  driver_signature: "Driver Signature",
  co_driver_name: "N/A",
  home_terminal: "Green Bay, WI",
  tractor_number: "TRK-100",
  trailer_numbers: "TRL-200",
  shipper_name: "Don's Paper Company",
  commodity: "Paper Products",
  load_id: "LOAD-0001",
};

function numberify(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export default function App() {
  const [form, setForm] = useState(initialForm);
  const [coords, setCoords] = useState({
    current: null,
    pickup: null,
    dropoff: null,
  });
  const [activeMapField, setActiveMapField] = useState("pickup");
  const [isResolvingMapPick, setIsResolvingMapPick] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [outputPanelHeight, setOutputPanelHeight] = useState(null);
  const [heroParallaxShift, setHeroParallaxShift] = useState(0);
  const formPanelRef = useRef(null);

  useEffect(() => {
    const onScroll = () => {
      const shift = Math.min(10, Math.max(0, window.scrollY * 0.05));
      setHeroParallaxShift(shift);
    };

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
    };
  }, []);

  useEffect(() => {
    const updatePanelHeight = () => {
      if (window.innerWidth <= 980) {
        setOutputPanelHeight(null);
        return;
      }

      const height = formPanelRef.current?.offsetHeight;
      setOutputPanelHeight(height ? `${height}px` : null);
    };

    updatePanelHeight();

    const observer = new ResizeObserver(() => {
      updatePanelHeight();
    });

    if (formPanelRef.current) {
      observer.observe(formPanelRef.current);
    }

    window.addEventListener("resize", updatePanelHeight);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", updatePanelHeight);
    };
  }, [result]);

  const routeSummary = useMemo(() => {
    if (!result?.route) {
      return null;
    }

    return {
      miles: Number(result.route.distance_miles || 0).toFixed(1),
      hours: Number(result.route.duration_hours || 0).toFixed(1),
      steps: result.route.steps || [],
    };
  }, [result]);

  function onChange(event) {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));

    if (name === "current_location") {
      setCoords((prev) => ({ ...prev, current: null }));
    }
    if (name === "pickup_location") {
      setCoords((prev) => ({ ...prev, pickup: null }));
    }
    if (name === "dropoff_location") {
      setCoords((prev) => ({ ...prev, dropoff: null }));
    }
  }

  async function onMapPick(latlng) {
    setError("");
    setIsResolvingMapPick(true);

    try {
      const resolved = await reverseGeocode(latlng.lat, latlng.lng);

      if (activeMapField === "current") {
        setForm((prev) => ({ ...prev, current_location: resolved.label }));
        setCoords((prev) => ({ ...prev, current: { lat: resolved.lat, lon: resolved.lon } }));
      }
      if (activeMapField === "pickup") {
        setForm((prev) => ({ ...prev, pickup_location: resolved.label }));
        setCoords((prev) => ({ ...prev, pickup: { lat: resolved.lat, lon: resolved.lon } }));
      }
      if (activeMapField === "dropoff") {
        setForm((prev) => ({ ...prev, dropoff_location: resolved.label }));
        setCoords((prev) => ({ ...prev, dropoff: { lat: resolved.lat, lon: resolved.lon } }));
      }
    } catch (err) {
      setError(err.message || "Map location resolve failed.");
    } finally {
      setIsResolvingMapPick(false);
    }
  }

  function applyPickedLocation(point) {
    const normalized = { lat: point.lat, lon: point.lon };

    if (activeMapField === "current") {
      setForm((prev) => ({ ...prev, current_location: point.label }));
      setCoords((prev) => ({ ...prev, current: normalized }));
      return;
    }
    if (activeMapField === "pickup") {
      setForm((prev) => ({ ...prev, pickup_location: point.label }));
      setCoords((prev) => ({ ...prev, pickup: normalized }));
      return;
    }
    setForm((prev) => ({ ...prev, dropoff_location: point.label }));
    setCoords((prev) => ({ ...prev, dropoff: normalized }));
  }

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const payload = {
        ...form,
        current_cycle_used_hours: numberify(form.current_cycle_used_hours),
        current_lat: coords.current?.lat,
        current_lon: coords.current?.lon,
        pickup_lat: coords.pickup?.lat,
        pickup_lon: coords.pickup?.lon,
        dropoff_lat: coords.dropoff?.lat,
        dropoff_lon: coords.dropoff?.lon,
      };
      const data = await planTrip(payload);
      setResult(data);
    } catch (err) {
      setError(err.message || "Failed to build trip plan.");
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="page-shell">
      <header className="hero-band panel-enter panel-enter-1" style={{ "--hero-shift": `${heroParallaxShift}px` }}>
        <div className="hero-content">
          <div className="hero-copy">
            <h1>HOS Trip Planner + ELD Log Generator</h1>
            <p className="subtitle">
              Generates a route, stop strategy, and day-by-day duty timeline using property-carrying
              70/8 assumptions.
            </p>
          </div>

          <div className="hero-visual" aria-hidden="true">
            <HeroIllustration />
          </div>
        </div>
      </header>

      <main className="layout-grid">
        <Card3D as="section" className="panel form-panel panel-enter panel-enter-2" ref={formPanelRef}>
          <h2>Trip Inputs</h2>
          <div className="map-pick-controls">
            <ChipToggle
              label="Select target field for map click:"
              value={activeMapField}
              onChange={setActiveMapField}
              options={[
                { label: "Current", value: "current" },
                { label: "Pickup", value: "pickup" },
                { label: "Dropoff", value: "dropoff" },
              ]}
            />
          </div>

          <LocationSelectorMap
            activeField={activeMapField}
            locations={coords}
            onPick={onMapPick}
            onSearchPick={applyPickedLocation}
          />
          {isResolvingMapPick ? <p className="muted">Resolving selected map point...</p> : null}

          <form onSubmit={onSubmit}>
            <label>
              Current location
              <input
                name="current_location"
                value={form.current_location}
                onChange={onChange}
                required
              />
            </label>

            <label>
              Pickup location
              <input
                name="pickup_location"
                value={form.pickup_location}
                onChange={onChange}
                required
              />
            </label>

            <label>
              Dropoff location
              <input
                name="dropoff_location"
                value={form.dropoff_location}
                onChange={onChange}
                required
              />
            </label>

            <label>
              Current cycle used (hours)
              <input
                name="current_cycle_used_hours"
                type="number"
                min="0"
                max="70"
                step="0.5"
                value={form.current_cycle_used_hours}
                onChange={onChange}
                required
              />
            </label>

            <details className="meta-details">
              <summary>Driver and shipment log details (optional)</summary>
              <div className="meta-grid">
                <label>
                  Driver number
                  <input name="driver_number" value={form.driver_number} onChange={onChange} />
                </label>
                <label>
                  Driver initials
                  <input name="driver_initials" value={form.driver_initials} onChange={onChange} />
                </label>
                <label>
                  Driver signature
                  <input name="driver_signature" value={form.driver_signature} onChange={onChange} />
                </label>
                <label>
                  Co-driver
                  <input name="co_driver_name" value={form.co_driver_name} onChange={onChange} />
                </label>
                <label>
                  Home terminal
                  <input name="home_terminal" value={form.home_terminal} onChange={onChange} />
                </label>
                <label>
                  Tractor number
                  <input name="tractor_number" value={form.tractor_number} onChange={onChange} />
                </label>
                <label>
                  Trailer numbers
                  <input name="trailer_numbers" value={form.trailer_numbers} onChange={onChange} />
                </label>
                <label>
                  Shipper
                  <input name="shipper_name" value={form.shipper_name} onChange={onChange} />
                </label>
                <label>
                  Commodity
                  <input name="commodity" value={form.commodity} onChange={onChange} />
                </label>
                <label>
                  Load ID
                  <input name="load_id" value={form.load_id} onChange={onChange} />
                </label>
              </div>
            </details>

            <button className={isLoading ? "btn-cta" : "btn-cta btn-cta-pulse"} disabled={isLoading} type="submit">
              {isLoading ? "Planning..." : "Generate Plan"}
            </button>
          </form>

          <div className="assumptions">
            <h3>Scenario Assumptions</h3>
            <ul>
              <li>Property-carrying, 70 hours / 8 days</li>
              <li>No adverse driving condition exception</li>
              <li>Fueling at least every 1000 miles</li>
              <li>1 hour pickup + 1 hour drop-off</li>
            </ul>
          </div>
        </Card3D>

        <Card3D
          as="section"
          className="panel output-panel panel-enter panel-enter-3"
          style={outputPanelHeight ? { height: outputPanelHeight } : undefined}
        >
          <h2>Route + Compliance Output</h2>
          {error ? <p className="error">{error}</p> : null}

          <RouteMap geometry={result?.route?.geometry} locations={result?.locations} />

          {routeSummary ? (
            <div className="metrics-row">
              <article>
                <p className="metric-label">Distance</p>
                <p className="metric-value">{routeSummary.miles} mi</p>
              </article>
              <article>
                <p className="metric-label">Drive time</p>
                <p className="metric-value">{routeSummary.hours} hr</p>
              </article>
              <article>
                <p className="metric-label">Estimated days</p>
                <p className="metric-value">{result?.compliance?.estimated_days ?? "-"}</p>
              </article>
            </div>
          ) : (
            <p className="muted">No route generated yet.</p>
          )}

          <div className="steps-panel">
            <h3>Route Instructions</h3>
            <ol>
              {(routeSummary?.steps || []).map((step, index) => (
                <li
                  key={`${index}-${step.instruction}`}
                  className="step-enter"
                  style={{ "--step-i": Math.min(index, 24) }}
                >
                  {step.instruction} ({step.distance_miles} mi, {step.duration_minutes} min)
                </li>
              ))}
            </ol>
          </div>
        </Card3D>
      </main>

      <Card3D as="section" className="panel logs-panel panel-enter panel-enter-4">
        <h2>Daily Logs (Preview)</h2>
        <DailyLogTable logs={result?.daily_logs || []} />
      </Card3D>
    </div>
  );
}
