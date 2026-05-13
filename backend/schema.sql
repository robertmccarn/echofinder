-- EchoFinder Initial Schema Draft

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    spotify_user_id VARCHAR(255) UNIQUE,
    email VARCHAR(255) UNIQUE,
    display_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Artists table (Main cache for artist metadata)
CREATE TABLE IF NOT EXISTS artists (
    artist_id SERIAL PRIMARY KEY,
    spotify_artist_id VARCHAR(255) UNIQUE,
    musicbrainz_artist_id VARCHAR(255) UNIQUE,
    lastfm_artist_id VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    country VARCHAR(100),
    begin_date DATE,
    first_release_date DATE,
    first_verified_activity_date DATE,
    breakout_date DATE,
    active_status VARCHAR(50),
    genres JSONB, -- Array of genres
    tags JSONB,   -- Array of tags
    images JSONB, -- List of image URLs
    spotify_url TEXT,
    external_urls JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Search Sessions
CREATE TABLE IF NOT EXISTS search_sessions (
    search_session_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    search_mode VARCHAR(50), -- 'spotify', 'artist', 'genre', 'scene'
    query_text TEXT,
    emergence_window VARCHAR(50),
    activity_filter VARCHAR(50),
    success_filter VARCHAR(50),
    similarity_filter VARCHAR(50),
    novelty_filter VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed Artists (Artists that anchor the search)
CREATE TABLE IF NOT EXISTS seed_artists (
    seed_artist_id SERIAL PRIMARY KEY,
    search_session_id INTEGER REFERENCES search_sessions(search_session_id),
    artist_id INTEGER REFERENCES artists(artist_id),
    source VARCHAR(50), -- 'spotify', 'manual'
    weight FLOAT DEFAULT 1.0,
    excluded_flag BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Candidate Artists (Results of a search)
CREATE TABLE IF NOT EXISTS candidate_artists (
    candidate_artist_id SERIAL PRIMARY KEY,
    search_session_id INTEGER REFERENCES search_sessions(search_session_id),
    artist_id INTEGER REFERENCES artists(artist_id),
    style_similarity_score FLOAT,
    scene_lineage_score FLOAT,
    mood_fit_score FLOAT,
    activity_score FLOAT,
    traction_score FLOAT,
    recent_emergence_score FLOAT,
    echo_score FLOAT,
    success_tier VARCHAR(50),
    emergence_confidence_label VARCHAR(50),
    explanation_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Artist Signals (Raw data points for scoring)
CREATE TABLE IF NOT EXISTS artist_signals (
    signal_id SERIAL PRIMARY KEY,
    artist_id INTEGER REFERENCES artists(artist_id),
    signal_type VARCHAR(100), -- 'release', 'tour', 'playlist', 'traction'
    signal_source VARCHAR(100), -- 'spotify', 'musicbrainz', 'lastfm'
    signal_value JSONB,
    signal_date DATE,
    confidence FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Recommendation Feedback
CREATE TABLE IF NOT EXISTS recommendation_feedback (
    feedback_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    search_session_id INTEGER REFERENCES search_sessions(search_session_id),
    candidate_artist_id INTEGER REFERENCES candidate_artists(candidate_artist_id),
    action VARCHAR(50), -- 'thumb_up', 'thumb_down', 'save', 'ignore'
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
