from flask import Blueprint, render_template, session, redirect, url_for, request
import requests
import spotipy
import pickle
import os
import random
import logging
from config import sp_oauth, LASTFM_API_KEY
from bs4 import BeautifulSoup
views = Blueprint('views', __name__)

# Set up logging
logger = logging.getLogger(__name__)

# Get the base directory of the current script
base_dir = os.path.dirname(os.path.abspath(__file__))

# Create absolute paths to the .pkl files
df_path = os.path.join(base_dir, 'df.pkl')
similarity_path = os.path.join(base_dir, 'similarity.pkl')

# Load the .pkl files using the absolute paths
music = pickle.load(open(df_path, 'rb'))
similarity = pickle.load(open(similarity_path, 'rb'))

LASTFM_BASE_URL = 'http://ws.audioscrobbler.com/2.0/'

# Function to roast top songs using the Gemini API
def roast_top_songs_with_gemini(songs):
    gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    gemini_api_key = "AIzaSyCJ4iYuf0Pq6xTjv91XElINsRE73VZ9gyQ"

    prompt_text = f"Roast these top songs: {', '.join(songs)}"
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt_text}]
            }
        ]
    }

    response = requests.post(
        f"{gemini_url}?key={gemini_api_key}",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        data = response.json()
        if "contents" in data and data["contents"]:
            return data["contents"][0]["parts"][0].get("text", "No roast available.")
        else:
            return "Gemini API returned an unexpected response format."
    else:
        return f"Gemini API request failed with status {response.status_code}: {response.text}"

# function to scrape Billboard charts
def scrape_billboard_charts():
    url = "https://www.billboard.com/charts/hot-100/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        songs = []
        # Find all song entries (limit to top 10)
        chart_items = soup.find_all("div", class_="o-chart-results-list-row-container")[:10]
        
        for idx, item in enumerate(chart_items, 1):
            try:
                # Extract title and artist
                title_element = item.find("h3", class_="c-title")
                artist_element = item.find("span", class_="c-label")
                
                # Extract image if available
                image_element = item.find("img")
                image_url = image_element['src'] if image_element else None
                
                if title_element and artist_element:
                    songs.append({
                        "rank": idx,
                        "title": title_element.text.strip(),
                        "artist": artist_element.text.strip(),
                        "image": image_url or "static/default_album.jpg"
                    })
            except Exception as e:
                print(f"Error processing song {idx}: {e}")
                continue
                
        return songs
    except Exception as e:
        print(f"Error scraping Billboard charts: {e}")
        return []

# Function to recommend songs
def recommend_song(song_name):
    try:
        song_index = music[music['song'] == song_name].index[0]
    except IndexError:
        return ["Song not found in the dataset."]
    
    distances = list(enumerate(similarity[song_index]))
    sorted_distances = sorted(distances, key=lambda x: x[1], reverse=True)
    recommended_songs = [music.iloc[i[0]].song for i in sorted_distances[1:6]]
    
    return recommended_songs

# Function to get artist information from MusicBrainz
def get_random_artist_info():
    """Get random artist information from Last.fm"""
    try:
        # Get chart artists
        params = {
            'method': 'chart.gettopartists',
            'api_key': LASTFM_API_KEY,
            'format': 'json',
            'limit': 1000
        }
        
        response = requests.get(LASTFM_BASE_URL, params=params)
        result = response.json()
        
        if 'artists' not in result:
            return None
            
        # Select random artist
        random_artist = random.choice(result['artists']['artist'])
        artist_name = random_artist['name']
        
        # Get detailed artist info
        params = {
            'method': 'artist.getInfo',
            'artist': artist_name,
            'api_key': LASTFM_API_KEY,
            'format': 'json',
            'autocorrect': 1
        }
        
        response = requests.get(LASTFM_BASE_URL, params=params)
        artist_info = response.json()
        
        if 'artist' not in artist_info:
            return None
            
        artist_data = artist_info['artist']
        
        return {
            'name': artist_data['name'],
            'image_url': artist_data.get('image', [{}])[-1].get('#text'),
            'bio': artist_data.get('bio', {}).get('summary', '').split('<a href')[0],
            'listeners': artist_data.get('stats', {}).get('listeners', 'Unknown'),
            'playcount': artist_data.get('stats', {}).get('playcount', 'Unknown'),
            'tags': [tag['name'] for tag in artist_data.get('tags', {}).get('tag', [])[:3]]
        }
    except Exception as e:
        logger.error(f"Error getting random artist: {e}")
        return None

def get_random_song_info():
    """Get random song information from Last.fm"""
    try:
        # Get chart tracks
        params = {
            'method': 'chart.gettoptracks',
            'api_key': LASTFM_API_KEY,
            'format': 'json',
            'limit': 1000
        }
        
        response = requests.get(LASTFM_BASE_URL, params=params)
        result = response.json()
        
        if 'tracks' not in result:
            return None
            
        # Select random track
        random_track = random.choice(result['tracks']['track'])
        track_name = random_track['name']
        artist_name = random_track['artist']['name']
        
        # Get detailed track info
        params = {
            'method': 'track.getInfo',
            'track': track_name,
            'artist': artist_name,
            'api_key': LASTFM_API_KEY,
            'format': 'json',
            'autocorrect': 1
        }
        
        response = requests.get(LASTFM_BASE_URL, params=params)
        track_info = response.json()
        
        if 'track' not in track_info:
            return None
            
        track_data = track_info['track']
        
        # Get album info if available
        album_info = track_data.get('album', {})
        
        return {
            'title': track_data['name'],
            'artist': track_data['artist']['name'],
            'image_url': album_info.get('image', [{}])[-1].get('#text', random_track.get('image', [{}])[-1].get('#text')),
            'album': album_info.get('title', 'Unknown'),
            'listeners': track_data.get('listeners', 'Unknown'),
            'playcount': track_data.get('playcount', 'Unknown'),
            'duration': int(track_data.get('duration', 0)) // 1000,  # Convert to seconds
            'tags': [tag['name'] for tag in track_data.get('toptags', {}).get('tag', [])[:3]]
        }
    except Exception as e:
        logger.error(f"Error getting random song: {e}")
        return None

def get_fallback_data(type_='artist'):
    """Provide fallback data if API fails"""
    if type_ == 'artist':
        return {
            'name': 'Artist Unavailable',
            'image_url': url_for('static', filename='default_artist.jpg'),
            'bio': 'Artist information temporarily unavailable. Please try refreshing the page.',
            'listeners': 'Unknown',
            'playcount': 'Unknown',
            'tags': []
        }
    else:
        return {
            'title': 'Song Unavailable',
            'artist': 'Unknown Artist',
            'image_url': url_for('static', filename='default_album.jpg'),
            'album': 'Unknown',
            'listeners': 'Unknown',
            'playcount': 'Unknown',
            'duration': 0,
            'tags': []
        }

@views.route('/')
def landing_page():
    """Render landing page with random artist and song"""
    try:
        auth_url = sp_oauth.get_authorize_url()
        
        # Get artist and song info with fallbacks
        artist_info = get_random_artist_info() or get_fallback_data('artist')
        song_info = get_random_song_info() or get_fallback_data('track')
        
        return render_template(
            "landing_page.html",
            auth_url=auth_url,
            artist_info=artist_info,
            song_info=song_info
        )
    except Exception as e:
        logger.error(f"Error in landing page: {e}")
        return render_template(
            "landing_page.html",
            auth_url=sp_oauth.get_authorize_url(),
            artist_info=get_fallback_data('artist'),
            song_info=get_fallback_data('track')
        )

def get_song_album_cover_url(song_name, artist_name, sp=None):
    """
    Get album cover URL for a song using Spotify API.
    Returns a default image URL if the song isn't found.
    """
    default_image = url_for('static', filename='default_album.png')
    
    if not sp:
        token_info = session.get('token_info', None)
        if not token_info:
            return default_image
        sp = spotipy.Spotify(auth=token_info['access_token'])
    
    try:
        # Search for the track on Spotify
        query = f"track:{song_name} artist:{artist_name}"
        results = sp.search(q=query, type='track', limit=1)
        
        if results['tracks']['items']:
            # Get the album cover from the first result
            images = results['tracks']['items'][0]['album']['images']
            if images:
                return images[0]['url']
    except Exception as e:
        print(f"Error getting album cover for {song_name}: {e}")
    
    return default_image

@views.route('/show_top_items', methods=['GET', 'POST'])
def show_top_items():
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect(url_for('views.landing_page'))

    # Set up Spotipy client with token
    sp = spotipy.Spotify(auth=token_info['access_token'])

    # Fetch user's profile to display the username
    user_profile = sp.current_user()
    username = user_profile['display_name']

    # Fetch Billboard Hot 100 Chart
    top_chart_songs = scrape_billboard_charts()

    
    # Handle time range selection
    time_range = request.form.get('time_range', 'medium_term')

    # Fetch user's top artists and tracks
    top_artists = sp.current_user_top_artists(limit=10, time_range=time_range)['items']
    top_tracks = sp.current_user_top_tracks(limit=10, time_range=time_range)['items']

    top_song_names = [track['name'] for track in top_tracks]
    
    roast_message = roast_top_songs_with_gemini(top_song_names)

    # Pass music list to the template
    music_list = music['song'].values

    # Handle song recommendation logic
    selected_song = request.form.get('selected_song')
    recommendations_with_posters = []
    
    if selected_song:
        recommendations = recommend_song(selected_song)
        print(f"Selected Song: {selected_song}, Recommendations: {recommendations}")
        
        # Get album covers for recommended songs using the same Spotify client
        recommendations_with_posters = [
            (song, get_song_album_cover_url(
                song, 
                music[music['song'] == song]['artist'].values[0],
                sp
            )) 
            for song in recommendations
        ]

    # Handle playlist creation logic
    playlist_type = request.form.get('playlist_type')
    success_message = None

    if playlist_type:
        user_id = sp.current_user()['id']

        if playlist_type == 'top_tracks':
            top_tracks = sp.current_user_top_tracks(limit=50, time_range='medium_term')['items']
            track_uris = [track['uri'] for track in top_tracks]
            playlist_name = "My Top 50 Tracks"
        elif playlist_type == 'recommendations' and selected_song:
            recommended_songs = recommend_song(selected_song)
            track_uris = []
            for song in recommended_songs:
                query = f"track:{song} artist:{music[music['song'] == song]['artist'].values[0]}"
                result = sp.search(q=query, type='track', limit=1)
                if result['tracks']['items']:
                    track_uris.append(result['tracks']['items'][0]['uri'])
            playlist_name = "Recommended Songs Playlist"
        else:
            return redirect(url_for('views.show_top_items'))
    
        # Create the new playlist
        new_playlist = sp.user_playlist_create(user_id, playlist_name, public=False)
        playlist_id = new_playlist['id']

        # Add the tracks to the new playlist
        sp.playlist_add_items(playlist_id, track_uris)

        # Set success message
        success_message = f"Successfully created playlist: {playlist_name}"

    return render_template(
        'index.html',
        username=username,
        top_chart_songs=top_chart_songs,
        artists=top_artists,
        tracks=top_tracks,
        music_list=music_list,
        roast_message=roast_message,
        recommendations_with_posters=recommendations_with_posters,
        success_message=success_message,
    )