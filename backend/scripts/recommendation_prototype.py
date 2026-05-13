import os
import time
from datetime import datetime
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import musicbrainzngs
import pylast

load_dotenv()

# Setup Clients
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

musicbrainzngs.set_useragent("EchoFinder", "0.1.0", "your_email@example.com")

lastfm = pylast.LastFMNetwork(
    api_key=os.getenv("LASTFM_API_KEY"),
    api_secret=os.getenv("LASTFM_API_SECRET")
)

def get_artist_emergence(artist_name):
    """Check when an artist first appeared via MusicBrainz."""
    try:
        result = musicbrainzngs.search_artists(artist=artist_name, limit=1)
        if result['artist-list']:
            artist = result['artist-list'][0]
            begin_date = artist.get('life-span', {}).get('begin', 'Unknown')
            # Extract year
            if begin_date and begin_date != 'Unknown':
                year = int(begin_date.split('-')[0])
                return year
    except Exception:
        pass
    return None

def get_artist_tags(artist_name):
    """Retrieve top tags for an artist from Last.fm."""
    try:
        artist = lastfm.get_artist(artist_name)
        top_tags = artist.get_top_tags(limit=10)
        return set([t.item.name.lower() for t in top_tags])
    except Exception:
        return set()

def calculate_tag_similarity(seed_tags, candidate_tags):
    if not seed_tags or not candidate_tags:
        return 0
    intersection = seed_tags.intersection(candidate_tags)
    union = seed_tags.union(candidate_tags)
    return len(intersection) / len(union)

def get_modern_echoes(seed_artist_name):
    print(f"\n--- Finding Modern Echoes for: {seed_artist_name} ---")
    
    seed_tags = get_artist_tags(seed_artist_name)
    lfm_artist = lastfm.get_artist(seed_artist_name)
    
    # Get 1st degree connections
    similar_1st = lfm_artist.get_similar(limit=20)
    
    # Collect 2nd degree candidates (Deep Discovery)
    all_candidate_names = set()
    for item in similar_1st:
        all_candidate_names.add(item.item.name)
        # Deep crawl: Get similar of similar (limited to top 5 each for speed)
        try:
            sim2 = item.item.get_similar(limit=5)
            for s2 in sim2:
                all_candidate_names.add(s2.item.name)
        except Exception:
            continue

    candidates = []
    current_year = datetime.now().year
    
    print(f"Checking {len(all_candidate_names)} potential candidates across 1st and 2nd degree...")

    for candidate_name in all_candidate_names:
        # 1. Check Emergence
        emergence_year = get_artist_emergence(candidate_name)
        if not emergence_year: continue
            
        years_active = current_year - emergence_year
        
        # FILTER: Only artists emerged after 2012 for this discovery test
        if emergence_year < 2012: continue
        
        # 2. Match Logic
        candidate_tags = get_artist_tags(candidate_name)
        tag_sim = calculate_tag_similarity(seed_tags, candidate_tags)
        
        # Emergence: High (0-6 years), Med (7-12 years)
        emergence_bonus = 0
        if years_active <= 6:
            emergence_bonus = 40
        elif years_active <= 12:
            emergence_bonus = 20
            
        # Echo Score
        # Primary signal here is Tag Similarity (30%) + Emergence (40%) + Discovery Depth (Bonus)
        echo_score = (tag_sim * 100 * 0.6) + emergence_bonus
            
        candidates.append({
            "name": candidate_name,
            "year": emergence_year,
            "score": round(echo_score, 1),
            "age": years_active,
            "tags": list(candidate_tags)[:3]
        })
            
    # Sort and Print
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"{'Artist':<25} | {'Year':<6} | {'Score':<6} | {'Status/Tags'}")
    print("-" * 75)
    for c in candidates[:15]:
        status = "MODERN ECHO" if c['age'] <= 6 else "Recent"
        tags_str = ", ".join(c['tags'])
        print(f"{c['name']:<25} | {c['year']:<6} | {c['score']:<6} | {status:<12} [{tags_str}]")

if __name__ == "__main__":
    seeds = ["Manchester Orchestra", "Thrice", "The Decemberists"]
    for seed in seeds:
        get_modern_echoes(seed)
        time.sleep(1) # Rate limit protection
