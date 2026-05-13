import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import musicbrainzngs
import pylast

# Load environment variables
load_dotenv()

# --- CONFIGURATION & CONSTANTS ---
CURRENT_YEAR = datetime.now().year
EMERGENCE_WINDOW_YEARS = 5
MIN_EMERGENCE_YEAR = CURRENT_YEAR - EMERGENCE_WINDOW_YEARS

# Performance Tuning
FAST_MODE = True
ENABLE_SECOND_DEGREE_DISCOVERY = False if FAST_MODE else True

# Crawl Limits
MAX_SIMILAR_PER_SEED = 10 if FAST_MODE else 25
MAX_SIMILAR_2ND = 3 if FAST_MODE else 8
MAX_TOTAL_CANDIDATES = 60 if FAST_MODE else 200 # Increased slightly for pool
REQUEST_TIMEOUT = 10

# Scoring Thresholds
MIN_ECHO_SCORE = 30
BRIDGE_SCORE_THRESHOLD = 20

# Paths
MODERN_POOL_PATH = "backend/data/modern_candidate_pool.json"

# --- IN-MEMORY CACHING ---
cache = {
    "emergence": {},
    "tags": {},
    "similar": {}
}

# --- API CLIENT SETUP ---
def get_clients():
    clients = {}
    try:
        cid = os.getenv("SPOTIFY_CLIENT_ID")
        sec = os.getenv("SPOTIFY_CLIENT_SECRET")
        if cid and sec:
            clients['spotify'] = spotipy.Spotify(
                auth_manager=SpotifyClientCredentials(client_id=cid, client_secret=sec),
                requests_timeout=REQUEST_TIMEOUT
            )
    except Exception as e:
        print(f"Warning: Spotify client failed: {e}")

    try:
        musicbrainzngs.set_useragent("EchoFinder", "0.1.0", "your_email@example.com")
        clients['musicbrainz'] = musicbrainzngs
    except Exception as e:
        print(f"Warning: MusicBrainz failed: {e}")

    try:
        lkey = os.getenv("LASTFM_API_KEY")
        lsec = os.getenv("LASTFM_API_SECRET")
        if lkey and lsec:
            clients['lastfm'] = pylast.LastFMNetwork(api_key=lkey, api_secret=lsec)
    except Exception as e:
        print(f"Warning: Last.fm failed: {e}")

    return clients

CLIENTS = get_clients()

# --- DATA LOADING ---

def load_modern_candidate_pool():
    """Load manual candidates from JSON."""
    if not os.path.exists(MODERN_POOL_PATH):
        return []
    try:
        with open(MODERN_POOL_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load modern pool: {e}")
        return []

# --- HELPER FUNCTIONS ---

def get_artist_emergence(artist_name):
    if artist_name in cache["emergence"]:
        return cache["emergence"][artist_name]
    
    if 'musicbrainz' not in CLIENTS:
        return None

    try:
        result = CLIENTS['musicbrainz'].search_artists(artist=artist_name, limit=1)
        if result['artist-list']:
            artist = result['artist-list'][0]
            begin_date = artist.get('life-span', {}).get('begin', 'Unknown')
            if begin_date and begin_date != 'Unknown':
                year = int(begin_date.split('-')[0])
                cache["emergence"][artist_name] = year
                return year
    except Exception:
        pass
    
    cache["emergence"][artist_name] = None
    return None

def get_artist_tags(artist_name):
    if artist_name in cache["tags"]:
        return cache["tags"][artist_name]
    
    if 'lastfm' not in CLIENTS:
        return set()

    try:
        artist = CLIENTS['lastfm'].get_artist(artist_name)
        top_tags = artist.get_top_tags(limit=10)
        tags = set([t.item.name.lower() for t in top_tags])
        cache["tags"][artist_name] = tags
        return tags
    except Exception:
        return set()

def calculate_tag_similarity(seed_tags, candidate_tags):
    if not seed_tags or not candidate_tags:
        return 0
    intersection = seed_tags.intersection(candidate_tags)
    union = seed_tags.union(candidate_tags)
    return len(intersection) / len(union)

# --- CORE LOGIC ---

def run_discovery(seed_artist_name):
    phase_start = time.time()
    print(f"\n{'='*60}")
    print(f"RESEARCHING SEED: {seed_artist_name}")
    print(f"{'='*60}")
    
    if not CLIENTS.get('lastfm'):
        print("Error: Last.fm credentials missing.")
        return

    seed_tags = get_artist_tags(seed_artist_name)
    
    # 1. Expand Candidates from Multiple Sources
    print(f"[1/3] Gathering candidates (Fast Mode: {FAST_MODE})...")
    raw_candidates = {} # name -> {match_score, source, source_type}
    
    # Source A: Last.fm Similarity Graph
    try:
        lfm_artist = CLIENTS['lastfm'].get_artist(seed_artist_name)
        similar_1st = lfm_artist.get_similar(limit=MAX_SIMILAR_PER_SEED)
        
        for item in similar_1st:
            name = item.item.name
            raw_candidates[name] = {
                "match": float(item.match), 
                "source": seed_artist_name,
                "source_type": "Last.fm Graph"
            }
            
            if ENABLE_SECOND_DEGREE_DISCOVERY and len(raw_candidates) < MAX_TOTAL_CANDIDATES:
                try:
                    similar_2nd = item.item.get_similar(limit=MAX_SIMILAR_2ND)
                    for s2 in similar_2nd:
                        s2_name = s2.item.name
                        if s2_name not in raw_candidates:
                            raw_candidates[s2_name] = {
                                "match": float(s2.match) * 0.7, 
                                "source": name,
                                "source_type": "Bridge Graph"
                            }
                except Exception:
                    continue
    except Exception as e:
        print(f"Warning during graph crawl: {e}")

    # Source B: Manual Modern Candidate Pool
    modern_pool = load_modern_candidate_pool()
    pool_added = 0
    for artist in modern_pool:
        # Check if artist is related to the current seed
        is_related = seed_artist_name in artist.get('related_legacy_styles', [])
        
        if is_related and artist['name'] not in raw_candidates:
            # We assign a high "match" score from the pool because they are manually linked
            raw_candidates[artist['name']] = {
                "match": 0.9, 
                "source": seed_artist_name,
                "source_type": "Manual Pool",
                "manual_data": artist
            }
            pool_added += 1
            
    print(f"[STATS] Last.fm: {len(raw_candidates) - pool_added} | Manual Pool: {pool_added}")

    # 2. Analyzing and Scoring
    print(f"[2/3] Scoring {len(raw_candidates)} candidates...")
    
    results = {
        "Modern Echo": [],
        "Bridge Artist": [],
        "Excluded": 0
    }

    for name, data in raw_candidates.items():
        # A. Determine Emergence Year
        manual_data = data.get('manual_data')
        if manual_data:
            emergence_year = manual_data['first_known_year']
            candidate_tags = set(manual_data['tags'])
        else:
            emergence_year = get_artist_emergence(name)
            candidate_tags = get_artist_tags(name)
        
        is_in_window = emergence_year and emergence_year >= MIN_EMERGENCE_YEAR
        
        # B. Echo Score Calculation
        tag_sim = calculate_tag_similarity(seed_tags, candidate_tags)
        
        # Lineage/Match Score
        lineage_score = data['match']
        
        # Emergence Bonus
        emergence_bonus = 30 if is_in_window else 0
        
        # Total Score
        echo_score = (tag_sim * 100 * 0.5) + (lineage_score * 100 * 0.2) + emergence_bonus
        
        artist_info = {
            "name": name,
            "year": emergence_year or "Unknown",
            "score": round(echo_score, 1),
            "source": data['source'],
            "source_type": data['source_type'],
            "tags": list(candidate_tags)[:3],
            "note": manual_data.get('source_note', "Found via similarity graph") if manual_data else "Found via similarity graph"
        }

        if is_in_window:
            if echo_score >= MIN_ECHO_SCORE:
                results["Modern Echo"].append(artist_info)
            else:
                results["Excluded"] += 1
        else:
            if echo_score >= BRIDGE_SCORE_THRESHOLD:
                results["Bridge Artist"].append(artist_info)
            else:
                results["Excluded"] += 1

    # 3. Final Output
    print(f"[3/3] Classification Complete.")
    
    results["Modern Echo"].sort(key=lambda x: x['score'], reverse=True)
    results["Bridge Artist"].sort(key=lambda x: x['score'], reverse=True)

    def print_section(title, items):
        if not items: return
        print(f"\n>>> {title} ({len(items)})")
        print(f"{'Artist':<30} | {'Year':<6} | {'Score':<6} | {'Source':<15} | {'Note/Tags'}")
        print("-" * 100)
        for i in items[:8]:
            tags = ", ".join(i['tags'])
            print(f"{i['name']:<30} | {i['year']:<6} | {i['score']:<6} | {i['source_type']:<15} | {i['note']} [{tags}]")

    print_section("MODERN ECHOES (0-5 Year Scope)", results["Modern Echo"])
    print_section("BRIDGE ARTISTS (Legacy / Lineage)", results["Bridge Artist"])
    
    duration = round(time.time() - phase_start, 2)
    print(f"\n[STATS] Phase Duration: {duration}s | Excluded: {results['Excluded']}")

if __name__ == "__main__":
    seeds = ["Manchester Orchestra", "Thrice", "The Decemberists"]
    
    start_time = time.time()
    for seed in seeds:
        run_discovery(seed)
        time.sleep(0.5)
    
    total_duration = round(time.time() - start_time, 2)
    print(f"\n{'='*60}")
    print(f"TOTAL RUNTIME: {total_duration} seconds")
    print(f"FAST_MODE: {FAST_MODE} | 0-5 Year Scope: {MIN_EMERGENCE_YEAR}-{CURRENT_YEAR}")
    print(f"{'='*60}")
