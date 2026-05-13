import musicbrainzngs
import sys

# MusicBrainz requires a user agent
musicbrainzngs.set_useragent("EchoFinder", "0.1.0", "your_email@example.com")

def lookup_artist_musicbrainz(artist_name):
    print(f"\nSearching MusicBrainz for '{artist_name}'...")
    result = musicbrainzngs.search_artists(artist=artist_name, limit=5)
    
    artists = result['artist-list']
    if not artists:
        print(f"No MusicBrainz results for '{artist_name}'")
        return None
        
    for idx, artist in enumerate(artists):
        name = artist['name']
        mbid = artist['id']
        country = artist.get('country', 'N/A')
        begin_date = artist.get('life-span', {}).get('begin', 'Unknown')
        
        # Get tags/genres
        tags = [t['name'] for t in artist.get('tag-list', [])]
        
        print(f"{idx + 1}. {name}")
        print(f"   MBID: {mbid}")
        print(f"   Origin: {country}")
        print(f"   Begin Date: {begin_date}")
        print(f"   Tags: {', '.join(tags[:10])}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        test_artists = ["Manchester Orchestra", "Thrice", "The Decemberists"]
        for name in test_artists:
            lookup_artist_musicbrainz(name)
    else:
        lookup_artist_musicbrainz(" ".join(sys.argv[1:]))
