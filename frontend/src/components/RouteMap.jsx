import { MapContainer, Marker, Polyline, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";
import MapFrame from "./MapFrame";

import "leaflet/dist/leaflet.css";

const markerIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

function toLatLngPair(point) {
  return [point.lat, point.lon];
}

export default function RouteMap({ geometry, locations }) {
  if (!geometry?.coordinates?.length || !locations) {
    return (
      <MapFrame>
        <div className="map-empty">Submit a trip to view the route map.</div>
      </MapFrame>
    );
  }

  const path = geometry.coordinates.map(([lon, lat]) => [lat, lon]);
  const currentPos = toLatLngPair(locations.current);
  const pickupPos = toLatLngPair(locations.pickup);
  const dropoffPos = toLatLngPair(locations.dropoff);

  return (
    <MapFrame>
      <MapContainer center={pickupPos} zoom={5} className="map-canvas" scrollWheelZoom attributionControl={false}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

        <Marker icon={markerIcon} position={currentPos}>
          <Popup>Current Location</Popup>
        </Marker>
        <Marker icon={markerIcon} position={pickupPos}>
          <Popup>Pickup Location</Popup>
        </Marker>
        <Marker icon={markerIcon} position={dropoffPos}>
          <Popup>Dropoff Location</Popup>
        </Marker>

        <Polyline positions={path} color="#0f766e" weight={5} opacity={0.9} />
      </MapContainer>
    </MapFrame>
  );
}
