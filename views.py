from flask import Blueprint, render_template, session, redirect, url_for, request
#import requests
import spotipy
import billboard
import pickle
import os
import random
import musicbrainzngs # Import MusicBrainz API client
from config import sp_oauth 

views = Blueprint('views', __name__)

# Set up MusicBrainz client
musicbrainzngs.set_useragent("AudioJamApp", "1.0", "denismwangi10471@gmail.com")

# Get the base directory of the current script
base_dir = os.path.dirname(os.path.abspath(__file__))

# Create absolute paths to the .pkl files
df_path = os.path.join(base_dir, 'df.pkl')
similarity_path = os.path.join(base_dir, 'similarity.pkl')

# Load the .pkl files using the absolute paths
music = pickle.load(open(df_path, 'rb'))
similarity = pickle.load(open(similarity_path, 'rb'))

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
    result = musicbrainzngs.search_artists(query='a', limit=100)  # Use a broad query
    artists = result['artist-list']
    
    if artists:
        random_artist = random.choice(artists)  # Pick a random artist
        artist_info = {
            'name': random_artist['name'],
            'id': random_artist['id'],
            'country': random_artist.get('country', 'Unknown'),
            'begin_date': random_artist.get('begin', 'Unknown'),
            'end_date': random_artist.get('end', 'Unknown'),
            'image_url': random_artist.get('images', [{}])[0].get('image')  # Get the first image
        }
        return artist_info
    return None

def get_random_song_info():
    result = musicbrainzngs.search_recordings(query='a', limit=100)  # Use a broad query
    recordings = result['recording-list']
    
    if recordings:
        random_song = random.choice(recordings)  # Pick a random song
        song_info = {
            'title': random_song['title'],
            'id': random_song['id'],
            'artist': ', '.join([artist['name'] for artist in random_song.get('artist-credit', [])]),
            'length': random_song.get('length', 'Unknown'),
            'release_date': random_song.get('first-release-date', 'Unknown'),
            'image_url': random_song.get('release-group', {}).get('images', [{}])[0].get('image')  # Get the first image
        }
        return song_info
    return None

@views.route('/')
def landing_page():
    # Get the authorization URL from Spotify OAuth
    auth_url = sp_oauth.get_authorize_url()
    artist_info = get_random_artist_info()
    song_info = get_random_song_info()  # Get random song info
    return render_template("landing_page.html",auth_url=auth_url, artist_info=artist_info, song_info=song_info)

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
                return images[0]['url']  # Return the largest image URL
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
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
    chart = billboard.ChartData('hot-100', fetch=True, timeout=25, headers=headers)
    top_chart_songs = [{
        "rank": song.rank,
        "title": song.title,
        "artist": song.artist,
        "image": song.image,
        "weeks": song.weeks,
        "peak": song.peakPos
    } for song in chart[:10]]
    
    # Handle time range selection
    time_range = request.form.get('time_range', 'medium_term')

    # Fetch user's top artists and tracks
    top_artists = sp.current_user_top_artists(limit=10, time_range=time_range)['items']
    top_tracks = sp.current_user_top_tracks(limit=10, time_range=time_range)['items']

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
        recommendations_with_posters=recommendations_with_posters,
        success_message=success_message
    )