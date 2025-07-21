# 🎶 Playlist Transfer Tool

Easily transfer your Spotify playlists to YouTube with this automated Python tool. The script authenticates your Spotify account, retrieves your playlists and tracks, then creates a new YouTube playlist and searches for corresponding videos to add.

## 🚀 Features

- Authenticate and fetch Spotify playlists and songs
- Search for songs on YouTube
- Automatically create YouTube playlists
- Add songs to YouTube playlists
- Supports command-line usage with minimal setup

## 🛠️ Requirements

- Python 3.8+
- Spotify Developer Account
- YouTube Data API v3 credentials

## 📂 Project Structure

```plaintext
Playlist-transfer-tool/
├── main.py          # Main script to transfer playlists
├── .cache/          # OAuth token cache
├── .gitignore
