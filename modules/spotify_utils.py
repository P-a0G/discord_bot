import time

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from modules.utils import read_json

client_id = read_json("files/tokens.json")["spotify_client_id"]
client_secret = read_json("files/tokens.json")["spotify_secret"]


class SpotifyManager:
    def __init__(self):
        self.client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        self.sp = spotipy.Spotify(client_credentials_manager=self.client_credentials_manager)
        self.sp.trace = False  # Disable debug output

    def get_music_metadata(self, title: str, artist=None, limit=10) -> dict:
        query = f"track:{title}"
        if artist:
            query += f" artist:{artist}"

        results = self.sp.search(q=query, type="track", limit=limit)
        time.sleep(0.1)

        if results["tracks"]["items"]:
            track = results["tracks"]["items"][0]

            return {
                "title": track["name"],
                "artists": ", ".join(artist["name"] for artist in track["artists"]),
                "album": track["album"]["name"],
                "release_date": track["album"]["release_date"],
                "duration_ms": track["duration_ms"],
                "popularity": track["popularity"],
                "preview_url": track["preview_url"],
                "external_url": track["external_urls"]["spotify"],
                "album_art_url": track["album"]["images"][0]["url"]
            }

        return {}

    def get_sounds(self, artist: str, limit=1) -> list:
        results = self.sp.search(q=f"artist:{artist}", type="track", limit=limit)
        time.sleep(0.1)

        sounds = []
        for track in results["tracks"]["items"]:
            sounds.append({
                "title": track["name"],
                "artists": ", ".join(a["name"] for a in track["artists"]),
                "album": track["album"]["name"],
                "popularity": track["popularity"],
                "preview_url": track["preview_url"],
                "external_url": track["external_urls"]["spotify"]
            })

        return sounds


if __name__ == '__main__':
    print("id:", client_id)
    print("secret:", client_secret)

    spotify_manager = SpotifyManager()
    metadata = spotify_manager.get_music_metadata("Shape of You", "Ed Sheeran")

    print("Metadata for 'Shape of You' by Ed Sheeran:")
    if not metadata:
        print("No metadata found.")
    else:
        for key, value in metadata.items():
            print(f"\t{key}: {value}")

    print("Metadata for 'Rhyme Dust (Dimension Remix)' by The MK & Dom Dolla:")
    metadata = spotify_manager.get_music_metadata("Rhyme Dust (Dimension Remix)", "The MK & Dom Dolla")
    if not metadata:
        print("No metadata found.")
    else:
        for key, value in metadata.items():
            print(f"\t{key}: {value}")

    print("\nSounds by Ed Sheeran:")
    sounds = spotify_manager.get_sounds("Ed Sheeran", limit=20)
    for sound in sounds:
        print("\t", sound)
