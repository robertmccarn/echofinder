import os
import sys
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

# Load environment variables from .env if it exists
load_dotenv()

def get_spotify_client():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("Error: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env")
        sys.exit(1)
        
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    return spotipy.Spotify(auth_manager=auth_manager)

def lookup_artist(artist_name):
    sp = get_spotify_client()
    results = sp.search(q='artist:' + artist_name, type='artist', limit=5)
    
    artists = results['artists']['items']
    if not artists:
        print(f"No artists found for '{artist_name}'")
        return None
        
    print(f"\nResults for '{artist_name}':")
    for idx, artist in enumerate(artists):
        name = artist.get('name', 'Unknown')
        artist_id = artist.get('id', 'Unknown')
        genres = artist.get('genres', [])
        popularity = artist.get('popularity', 'N/A')
        spotify_url = artist.get('external_urls', {}).get('spotify', 'N/A')
        
        print(f"{idx + 1}. {name}")
        print(f"   ID: {artist_id}")
        print(f"   Genres: {', '.join(genres) if genres else 'None'}")
        print(f"   Popularity: {popularity}")
        print(f"   URL: {spotify_url}\n")
    
    return artists

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default test case from design doc
        test_artists = ["Manchester Orchestra", "Thrice", "The Decemberists"]
        for name in test_artists:
            lookup_artist(name)
    else:
        lookup_artist(" ".join(sys.argv[1:]))
