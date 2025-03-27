import spotipy
from spotipy.oauth2 import SpotifyOAuth
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import time
import os

# Constants
SPOTIPY_CLIENT_ID = "YOUR SPOTIFY CLIENT ID"
SPOTIPY_CLIENT_SECRET = "YOUR SPOTIFY CLIENT SECRET"
SPOTIPY_REDIRECT_URI = "http://localhost:8888/callback"
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

# Authenticate Spotify
def authenticate_spotify():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                                     client_secret=SPOTIPY_CLIENT_SECRET,
                                                     redirect_uri=SPOTIPY_REDIRECT_URI,
                                                     scope="playlist-read-private"))

# Authenticate YouTube
def authenticate_youtube():
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", YOUTUBE_SCOPES)
    creds = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=creds)

# Get Spotify Playlists
def get_spotify_playlists(sp):
    playlists = sp.current_user_playlists()
    return {idx + 1: (pl["name"], pl["id"]) for idx, pl in enumerate(playlists["items"])}

# Get Songs in a Playlist
def get_playlist_tracks(sp, playlist_id):
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    for idx, item in enumerate(results["items"], start=1):
        track = item["track"]
        tracks.append((idx, f"{track['name']} {track['artists'][0]['name']}"))
    return tracks

# Search for a Song on YouTube
def search_youtube_song(youtube, song_name):
    request = youtube.search().list(q=song_name, part="snippet", maxResults=1, type="video")
    response = request.execute()
    return response["items"][0]["id"]["videoId"] if response["items"] else None

# Get User's YouTube Playlists
def get_youtube_playlists(youtube):
    playlists = []
    request = youtube.playlists().list(
        part="snippet",
        mine=True,
        maxResults=50
    )
    while request:
        response = request.execute()
        playlists.extend(response.get("items", []))
        request = youtube.playlists().list_next(request, response)
    return {pl["snippet"]["title"]: pl["id"] for pl in playlists}

# Create YouTube Playlist
def create_youtube_playlist(youtube, name):
    request = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {"title": name, "description": "Imported from Spotify"},
            "status": {"privacyStatus": "public"}
        },
    )
    response = request.execute()
    return response["id"]

# Add Song to YouTube Playlist
def add_song_to_youtube_playlist(youtube, playlist_id, video_id):
    request = youtube.playlistItems().insert(
        part="snippet",
        body={"snippet": {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}}
    )
    request.execute()

# Interactive Playlist Selection
def select_playlists(playlists):
    print("\nAvailable Spotify Playlists:")
    for idx, (name, _) in playlists.items():
        print(f"{idx}. {name}")

    selected = input("\nEnter the numbers of the playlists you want to transfer (comma-separated): ")
    selected_indices = list(map(int, selected.split(",")))
    return {idx: playlists[idx] for idx in selected_indices}

# Interactive Song Selection
def select_songs(tracks):
    print("\nAvailable Songs:")
    for idx, track in tracks:
        print(f"{idx}. {track}")

    print("\nEnter 'all' to transfer all songs.")
    selected = input("Enter the numbers of the songs you want to transfer (comma-separated): ")
    
    if selected.lower() == "all":
        return [track[1] for track in tracks]

    selected_indices = list(map(int, selected.split(",")))
    return [tracks[idx - 1][1] for idx in selected_indices]

# Transfer Selected Playlists and Songs
def transfer_playlists(sp, youtube):
    spotify_playlists = get_spotify_playlists(sp)
    selected_playlists = select_playlists(spotify_playlists)

    # Fetch existing YouTube playlists
    youtube_playlists = get_youtube_playlists(youtube)

    for idx, (name, playlist_id) in selected_playlists.items():
        print(f"\nTransferring: {name}")

        # Check if the playlist already exists on YouTube
        if name in youtube_playlists:
            youtube_playlist_id = youtube_playlists[name]
            print(f"Playlist '{name}' already exists on YouTube. Adding songs to it.")
        else:
            # Create a new playlist if it doesn't exist
            youtube_playlist_id = create_youtube_playlist(youtube, name)
            print(f"Created new playlist '{name}' on YouTube.")

        # Get tracks from Spotify playlist
        tracks = get_playlist_tracks(sp, playlist_id)

        # Select songs to transfer
        selected_songs = select_songs(tracks)

        # Add selected songs to the YouTube playlist
        for song in selected_songs:
            video_id = search_youtube_song(youtube, song)
            if video_id:
                add_song_to_youtube_playlist(youtube, youtube_playlist_id, video_id)
                print(f"Added: {song}")
                time.sleep(1)  # Avoid rate limiting

# Main Function
def main():
    # Authenticate Spotify
    sp = authenticate_spotify()
    
    # Authenticate YouTube
    youtube = authenticate_youtube()
    
    # Run the Interactive Transfer
    transfer_playlists(sp, youtube)

if __name__ == "__main__":
    main()