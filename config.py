import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Define your Spotify app credentials here
SPOTIPY_CLIENT_ID = "fa46dfec5ae244f2b3c831aa00dfa7ed"
SPOTIPY_CLIENT_SECRET = "99318d0ed323485c9c9cc5e37e95a637"
SPOTIPY_REDIRECT_URI = "https://audiojam.onrender.com/callback"

# Scope defines the permissions you're requesting from the user
SCOPE="user-top-read playlist-modify-private playlist-modify-public",

# Set up the Spotify OAuth handler
sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                        client_secret=SPOTIPY_CLIENT_SECRET,
                        redirect_uri=SPOTIPY_REDIRECT_URI,
                        scope=SCOPE)

# Create an instance of Spotipy with token
spotify = spotipy.Spotify(auth_manager=sp_oauth)