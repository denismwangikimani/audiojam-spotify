import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Define your Spotify app credentials here
SPOTIPY_CLIENT_ID = "fa46dfec5ae244f2b3c831aa00dfa7ed"
SPOTIPY_CLIENT_SECRET = "99318d0ed323485c9c9cc5e37e95a637"
#SPOTIPY_REDIRECT_URI = "http://127.0.0.1:5000/callback"
SPOTIPY_REDIRECT_URI = "https://audiojam.onrender.com/callback"

# Scope defines the permissions you're requesting from the user
SCOPE="user-top-read playlist-modify-private playlist-modify-public"

# Last.fm Configuration
LASTFM_API_KEY = "be4d22047902076b9cba05313cf51847"
LASTFM_SHARED_SECRET = "38cc4d62e567b03c7c81aa8db1cc200b"
LASTFM_BASE_URL = 'http://ws.audioscrobbler.com/2.0/'

# Set up the Spotify OAuth handler
sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                        client_secret=SPOTIPY_CLIENT_SECRET,
                        redirect_uri=SPOTIPY_REDIRECT_URI,
                        scope=SCOPE)

# Create an instance of Spotipy with token
spotify = spotipy.Spotify(auth_manager=sp_oauth)