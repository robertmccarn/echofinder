const API_BASE =
  process.env.NEXT_PUBLIC_ECHOFINDER_API_BASE || "http://127.0.0.1:8000";

export async function fetchRecommendations(seed) {
  const url = `${API_BASE}/api/recommendations?seed=${encodeURIComponent(seed)}`;
  const response = await fetch(url, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store"
  });

  const data = await response.json();

  if (!response.ok) {
    const message =
      data?.error?.message || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return data;
}
