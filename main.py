import os
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Constants from .env
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

# ---------------- Spotify Authentication ----------------
def authenticate_spotify():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope="playlist-read-private"
    ))

# ---------------- YouTube Authentication ----------------
def authenticate_youtube():
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", YOUTUBE_SCOPES)
    creds = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=creds)

# ---------------- Spotify Functions ----------------
def get_spotify_playlists(sp):
    playlists = sp.current_user_playlists()
    return {idx + 1: (pl["name"], pl["id"]) for idx, pl in enumerate(playlists["items"])}

def get_playlist_tracks(sp, playlist_id):
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    while results:
        for idx, item in enumerate(results["items"], start=len(tracks) + 1):
            track = item["track"]
            if track:  # Ensure track is not None
                tracks.append((idx, f"{track['name']} {track['artists'][0]['name']}"))
        if results["next"]:
            results = sp.next(results)
        else:
            break
    return tracks

# ---------------- YouTube Functions ----------------
def search_youtube_song(youtube, song_name):
    request = youtube.search().list(q=song_name, part="snippet", maxResults=1, type="video")
    response = request.execute()
    return response["items"][0]["id"]["videoId"] if response["items"] else None

def get_youtube_playlists(youtube):
    playlists = []
    request = youtube.playlists().list(part="snippet", mine=True, maxResults=50)
    while request:
        response = request.execute()
        playlists.extend(response.get("items", []))
        request = youtube.playlists().list_next(request, response)
    return {pl["snippet"]["title"]: pl["id"] for pl in playlists}

def create_youtube_playlist(youtube, name):
    request = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {"title": name, "description": "Imported from Spotify"},
            "status": {"privacyStatus": "public"}
        }
    )
    response = request.execute()
    return response["id"]

def add_song_to_youtube_playlist(youtube, playlist_id, video_id):
    request = youtube.playlistItems().insert(
        part="snippet",
        body={"snippet": {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}}
    )
    request.execute()

def get_videos_in_youtube_playlist(youtube, playlist_id):
    video_ids = set()
    request = youtube.playlistItems().list(
        part="contentDetails",
        playlistId=playlist_id,
        maxResults=50
    )
    while request:
        response = request.execute()
        for item in response.get("items", []):
            video_ids.add(item["contentDetails"]["videoId"])
        request = youtube.playlistItems().list_next(request, response)
    return video_ids

# ---------------- User Interaction ----------------
def select_playlists(playlists):
    print("\nAvailable Spotify Playlists:")
    for idx, (name, _) in playlists.items():
        print(f"{idx}. {name}")

    selected = input("\nEnter the numbers of the playlists you want to transfer (comma-separated): ")
    selected_indices = list(map(int, selected.split(",")))
    return {idx: playlists[idx] for idx in selected_indices}

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

# ---------------- Main Transfer Logic ----------------
def transfer_playlists(sp, youtube):
    spotify_playlists = get_spotify_playlists(sp)
    selected_playlists = select_playlists(spotify_playlists)

    youtube_playlists = get_youtube_playlists(youtube)

    for idx, (name, playlist_id) in selected_playlists.items():
        print(f"\nTransferring: {name}")

        if name in youtube_playlists:
            youtube_playlist_id = youtube_playlists[name]
            print(f"Playlist '{name}' already exists on YouTube. Adding songs to it.")
        else:
            youtube_playlist_id = create_youtube_playlist(youtube, name)
            print(f"Created new playlist '{name}' on YouTube.")

        tracks = get_playlist_tracks(sp, playlist_id)
        selected_songs = select_songs(tracks)
        existing_video_ids = get_videos_in_youtube_playlist(youtube, youtube_playlist_id)

        for song in selected_songs:
            video_id = search_youtube_song(youtube, song)
            if video_id:
                if video_id not in existing_video_ids:
                    add_song_to_youtube_playlist(youtube, youtube_playlist_id, video_id)
                    print(f"Added: {song}")
                    time.sleep(1)  # avoid hitting API limits
                else:
                    print(f"Skipped (already exists): {song}")

# ---------------- Main Entry ----------------
def main():
    sp = authenticate_spotify()
    youtube = authenticate_youtube()
    transfer_playlists(sp, youtube)

if __name__ == "__main__":
    main()
