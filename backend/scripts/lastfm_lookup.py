import os
import sys
import pylast
from dotenv import load_dotenv

load_dotenv()

def get_lastfm_network():
    api_key = os.getenv("LASTFM_API_KEY")
    api_secret = os.getenv("LASTFM_API_SECRET")
    
    if not api_key or not api_secret:
        print("Error: LASTFM_API_KEY and LASTFM_API_SECRET must be set in .env")
        return None
        
    return pylast.LastFMNetwork(api_key=api_key, api_secret=api_secret)

def lookup_artist_lastfm(artist_name):
    network = get_lastfm_network()
    if not network:
        return
        
    artist = network.get_artist(artist_name)
    
    try:
        # Check if artist exists by trying to get top tags
        top_tags = artist.get_top_tags(limit=10)
        similar_artists = artist.get_similar(limit=5)
        
        print(f"\nResults for '{artist_name}' on Last.fm:")
        print(f"   Tags: {', '.join([t.item.name for t in top_tags])}")
        print(f"   Similar Artists: {', '.join([a.item.name for a in similar_artists])}")
        
    except Exception as e:
        print(f"Error searching for '{artist_name}' on Last.fm: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        test_artists = ["Manchester Orchestra", "Thrice", "The Decemberists"]
        for name in test_artists:
            lookup_artist_lastfm(name)
    else:
        lookup_artist_lastfm(" ".join(sys.argv[1:]))
