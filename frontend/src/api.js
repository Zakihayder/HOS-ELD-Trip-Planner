const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) {
    throw new Error("Backend health check failed.");
  }
  const data = await response.json();
  if (data.status !== "ok") {
    throw new Error("Backend is not healthy.");
  }
  return data;
}

export async function planTrip(payload) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/plan-trip`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new Error(
      "Cannot reach backend API. Start Django server at http://127.0.0.1:8000 and try again.",
    );
  }

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Failed to generate plan");
  }

  return data;
}

export async function reverseGeocode(lat, lon) {
  const url = `${API_BASE_URL}/api/reverse-geocode?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`;
  const response = await fetch(url);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Unable to resolve clicked map location.");
  }
  return data;
}

export async function geocodeSearch(query) {
  const url = `${API_BASE_URL}/api/geocode?q=${encodeURIComponent(query)}`;
  const response = await fetch(url);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Unable to find the searched location.");
  }
  return data;
}

export async function geocodeSuggest(query) {
  const url = `${API_BASE_URL}/api/geocode-suggest?q=${encodeURIComponent(query)}`;
  const response = await fetch(url);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Unable to load location suggestions.");
  }
  return Array.isArray(data) ? data : [];
}
