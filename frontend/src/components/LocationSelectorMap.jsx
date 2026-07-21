import { useEffect, useMemo, useState } from "react";
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import MapFrame from "./MapFrame";

import { geocodeSearch, geocodeSuggest } from "../api";

import "leaflet/dist/leaflet.css";

const markerIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

function ClickCapture({ onPick }) {
  useMapEvents({
    click(event) {
      onPick(event.latlng);
    },
  });

  return null;
}

function MapViewController({ focusPoint }) {
  const map = useMap();

  useEffect(() => {
    if (!focusPoint) {
      return;
    }
    map.flyTo([focusPoint.lat, focusPoint.lon], Math.max(map.getZoom(), 10), {
      duration: 0.8,
    });
  }, [focusPoint, map]);

  return null;
}

function markerFromPoint(point) {
  if (!point || typeof point.lat !== "number" || typeof point.lon !== "number") {
    return null;
  }
  return [point.lat, point.lon];
}

export default function LocationSelectorMap({ locations, activeField, onPick, onSearchPick }) {
  const [searchText, setSearchText] = useState("");
  const [searchError, setSearchError] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [focusPoint, setFocusPoint] = useState(null);
  const [activeSuggestionIndex, setActiveSuggestionIndex] = useState(-1);

  const normalizedQuery = useMemo(() => searchText.trim(), [searchText]);

  const current = markerFromPoint(locations.current);
  const pickup = markerFromPoint(locations.pickup);
  const dropoff = markerFromPoint(locations.dropoff);

  useEffect(() => {
    if (normalizedQuery.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      setActiveSuggestionIndex(-1);
      return;
    }

    let cancelled = false;
    const timer = setTimeout(async () => {
      try {
        const items = await geocodeSuggest(normalizedQuery);
        if (!cancelled) {
          setSuggestions(items);
          setShowSuggestions(items.length > 0);
          setActiveSuggestionIndex(items.length > 0 ? 0 : -1);
        }
      } catch {
        if (!cancelled) {
          setSuggestions([]);
          setShowSuggestions(false);
          setActiveSuggestionIndex(-1);
        }
      }
    }, 250);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [normalizedQuery]);

  function applyPoint(point) {
    onSearchPick(point);
    setFocusPoint({ lat: point.lat, lon: point.lon });
  }

  function onSuggestionClick(item) {
    setSearchText(item.label);
    setShowSuggestions(false);
    setSuggestions([]);
    setActiveSuggestionIndex(-1);
    applyPoint(item);
  }

  function onSearchInputKeyDown(event) {
    if (!showSuggestions || suggestions.length === 0) {
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveSuggestionIndex((prev) => (prev + 1) % suggestions.length);
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveSuggestionIndex((prev) => (prev <= 0 ? suggestions.length - 1 : prev - 1));
      return;
    }

    if (event.key === "Enter" && activeSuggestionIndex >= 0) {
      event.preventDefault();
      onSuggestionClick(suggestions[activeSuggestionIndex]);
      return;
    }

    if (event.key === "Escape") {
      setShowSuggestions(false);
    }
  }

  async function onSearchSubmit(event) {
    event.preventDefault();
    setSearchError("");
    const query = searchText.trim();
    if (!query) {
      setSearchError("Type a location to search.");
      return;
    }

    setIsSearching(true);
    try {
      const found = await geocodeSearch(query);
      setShowSuggestions(false);
      setSuggestions([]);
      applyPoint(found);
    } catch (err) {
      setSearchError(err.message || "Search failed.");
    } finally {
      setIsSearching(false);
    }
  }

  return (
    <div>
      <form className="map-search" onSubmit={onSearchSubmit}>
        <input
          type="text"
          placeholder="Search location (city, address, or lat,lon)"
          value={searchText}
          onChange={(event) => {
            setSearchText(event.target.value);
            setSearchError("");
          }}
          onKeyDown={onSearchInputKeyDown}
          onFocus={() => {
            if (suggestions.length > 0) {
              setShowSuggestions(true);
            }
          }}
        />
        <button type="submit" className="map-search-btn" disabled={isSearching}>
          {isSearching ? "Searching..." : "Search"}
        </button>
      </form>
      {showSuggestions ? (
        <ul className="suggestions-list">
          {suggestions.map((item) => (
            <li key={`${item.lat}-${item.lon}-${item.label}`}>
              <button
                type="button"
                className={`suggestion-item${activeSuggestionIndex >= 0 && suggestions[activeSuggestionIndex] === item ? " active" : ""}`}
                onClick={() => onSuggestionClick(item)}
              >
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {searchError ? <p className="error">{searchError}</p> : null}
      <MapFrame compact>
        <MapContainer
          center={[39.5, -98.35]}
          zoom={4}
          className="map-canvas"
          scrollWheelZoom
          dragging
          touchZoom
          doubleClickZoom
          boxZoom
          keyboard
          attributionControl={false}
        >
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <MapViewController focusPoint={focusPoint} />
          <ClickCapture onPick={onPick} />

          {current ? <Marker icon={markerIcon} position={current} /> : null}
          {pickup ? <Marker icon={markerIcon} position={pickup} /> : null}
          {dropoff ? <Marker icon={markerIcon} position={dropoff} /> : null}
        </MapContainer>
      </MapFrame>
    </div>
  );
}
