"use client";

import { useMemo, useState } from "react";
import Image from "next/image";
import { fetchRecommendations } from "@/lib/api";

function RecList({ title, items = [] }) {
  const safeItems = Array.isArray(items) ? items : [];
  const emptyLabel =
    title === "Modern Echoes"
      ? "No Modern Echoes found for this seed yet."
      : "No Bridge Artists found for this seed yet.";

  return (
    <section className="card">
      <h2>
        {title} <span className="muted">({safeItems.length})</span>
      </h2>
      {safeItems.length === 0 ? (
        <p className="muted">{emptyLabel}</p>
      ) : (
        <ul className="list">
          {safeItems.map((item, idx) => (
            <li key={`${item.artist_name}-${idx}`} className="listItem">
              <div className="itemHeader">
                {item.image_url ? (
                  <img
                    src={item.image_url}
                    alt={`${item.artist_name} artist`}
                    className="artistThumb"
                    loading="lazy"
                  />
                ) : (
                  <div className="artistThumb placeholder" aria-hidden="true">
                    ♪
                  </div>
                )}
                <div className="itemTitle">
                  {item.artist_name} <span className="score">{item.echo_score}</span>
                </div>
              </div>
              <div className="metaRow">
                <span className="pill">Emergence: {item.emergence_year ?? "Unknown"}</span>
                <span className="pill">Score: {item.echo_score}</span>
              </div>
              <div className="metaRow">
                <span className="pill">
                  Shared tags:{" "}
                  {item.shared_tags && item.shared_tags.length > 0
                    ? item.shared_tags.join(", ")
                    : "None"}
                </span>
              </div>
              <div className="metaRow">
                <span className="pill">
                  Sources:{" "}
                  {item.sources && item.sources.length > 0
                    ? item.sources.join(", ")
                    : "Unknown"}
                </span>
              </div>
              <p className="muted">{item.source_note || "No explanation provided."}</p>
              {item.spotify_url ? (
                <a
                  href={item.spotify_url}
                  target="_blank"
                  rel="noreferrer"
                  className="spotifyLink"
                >
                  Open in Spotify
                </a>
              ) : (
                <span className="muted">Spotify link unavailable</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function HomePage() {
  const [seed, setSeed] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  const isEmptyResult = useMemo(() => {
    if (!result) return false;
    const modern = Array.isArray(result.modern_echoes) ? result.modern_echoes : [];
    const bridge = Array.isArray(result.bridge_artists) ? result.bridge_artists : [];
    return modern.length === 0 && bridge.length === 0;
  }, [result]);

  async function onSubmit(event) {
    event.preventDefault();
    const trimmed = seed.trim();
    if (!trimmed) {
      setSubmitted(true);
      setError("Enter a legacy artist to search.");
      setResult(null);
      return;
    }

    setSubmitted(true);
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await fetchRecommendations(trimmed);
      setResult(data);
    } catch (err) {
      const message = err?.message || "Unknown error";
      if (message.toLowerCase() === "failed to fetch") {
        setError(
          "Unable to reach the backend API. Make sure FastAPI is running at http://127.0.0.1:8000 and try again."
        );
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <div className="hero">
        <div className="brandRow">
          <div className="logoBadge" aria-hidden="true">
            <Image
              src="/brand/echofinder-logo-mark.png"
              alt=""
              width={44}
              height={44}
              className="logoImage"
              priority
            />
          </div>
          <div>
            <p className="eyebrow">EchoFinder v3 Manual Web MVP</p>
            <p className="wordmark">EchoFinder</p>
          </div>
        </div>
        <h1>Find The Modern Echo</h1>
        <p className="muted">
          Enter a legacy artist to discover active modern echoes and lineage bridge
          artists with explainable recommendation metadata.
        </p>
      </div>

      <form className="searchForm" onSubmit={onSubmit}>
        <label htmlFor="seed" className="label">
          Legacy artist
        </label>
        <div className="searchRow">
          <input
            id="seed"
            name="legacy-seed"
            autoComplete="off"
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
            placeholder="Enter a legacy artist"
            className="input"
          />
          <button type="submit" className="button" disabled={loading}>
            {loading ? "Searching..." : "Find recommendations"}
          </button>
        </div>
      </form>

      {loading && (
        <section className="card">
          <h2>Loading</h2>
          <p className="muted">Fetching recommendations from backend...</p>
        </section>
      )}

      {!loading && error && (
        <section className="card errorCard">
          <h2>Error</h2>
          <p>{error}</p>
        </section>
      )}

      {!loading && !error && submitted && isEmptyResult && (
        <section className="card">
          <h2>Empty result</h2>
          <p className="muted">
            No recommendations returned for this seed. Try another artist, or
            re-check the exact seed name.
          </p>
        </section>
      )}

      {!loading && !error && result && (
        <div className="grid">
          <RecList title="Modern Echoes" items={result.modern_echoes} />
          <RecList title="Bridge Artists" items={result.bridge_artists} />
        </div>
      )}
    </main>
  );
}
