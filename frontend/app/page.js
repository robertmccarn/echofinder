"use client";

import { useMemo, useState } from "react";
import { fetchRecommendations } from "@/lib/api";

function RecList({ title, items }) {
  return (
    <section className="card">
      <h2>
        {title} <span className="muted">({items.length})</span>
      </h2>
      {items.length === 0 ? (
        <p className="muted">
          No artists in this section for the current seed. Try another seed or
          adjust the modern window in backend requests.
        </p>
      ) : (
        <ul className="list">
          {items.map((item, idx) => (
            <li key={`${item.artist_name}-${idx}`} className="listItem">
              <div className="itemTitle">
                {item.artist_name} <span className="score">{item.echo_score}</span>
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
    return result.modern_echoes.length === 0 && result.bridge_artists.length === 0;
  }, [result]);

  async function onSubmit(event) {
    event.preventDefault();
    const trimmed = seed.trim();
    if (!trimmed) return;

    setSubmitted(true);
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await fetchRecommendations(trimmed);
      setResult(data);
    } catch (err) {
      setError(err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <div className="hero">
        <p className="eyebrow">EchoFinder v3 Manual Web MVP</p>
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
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
            placeholder="Manchester Orchestra"
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
