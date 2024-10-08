from flask import Blueprint, render_template, session, redirect, url_for, request
import spotipy
import billboard
import pickle
import os
import random
from config import sp_oauth 

views = Blueprint('views', __name__)

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

# Function to get the album cover URL of a song
def get_song_album_cover_url(song_name, artist_name):
    # Set up Spotipy client
    sp = spotipy.Spotify(auth_manager=sp_oauth)
    
    # Search for the song on Spotify
    query = f"track:{song_name} artist:{artist_name}"
    results = sp.search(q=query, type='track', limit=1)
    
    # Extract the album cover URL if the song is found
    if results['tracks']['items']:
        album_cover_url = results['tracks']['items'][0]['album']['images'][0]['url']
        return album_cover_url
    else:
        return None

@views.route('/')
def landing_page():
    auth_url = sp_oauth.get_authorize_url()

    # Set up Spotipy client
    sp = spotipy.Spotify(auth_manager=sp_oauth)
    
    # Fetch a random artist from the user's top artists
    top_artists = sp.current_user_top_artists(limit=50)['items']
    
    if top_artists:
        artist_of_the_day = random.choice(top_artists)
        artist_info = {
            "name": artist_of_the_day['name'],
            "image": artist_of_the_day['images'][0]['url'] if artist_of_the_day['images'] else None,
            "popularity": artist_of_the_day['popularity'],
            "genres": ", ".join(artist_of_the_day['genres']),
            "followers": artist_of_the_day['followers']['total']
        }
    else:
        artist_info = {
            "name": "Unknown Artist",
            "image": None,
            "popularity": "N/A",
            "genres": "N/A",
            "followers": "N/A"
        }

    # Fetch a random song from the user's top tracks
    top_tracks = sp.current_user_top_tracks(limit=50)['items']
    
    if top_tracks:
        song_of_the_day = random.choice(top_tracks)
        song_info = {
            "name": song_of_the_day['name'],
            "artist": ", ".join([artist['name'] for artist in song_of_the_day['artists']]),
            "album": song_of_the_day['album']['name'],
            "image": song_of_the_day['album']['images'][0]['url'] if song_of_the_day['album']['images'] else None,
            "streams": song_of_the_day['popularity'], 
            "genres": "N/A"  
        }
    else:
        song_info = {
            "name": "Unknown Song",
            "artist": "Unknown Artist",
            "album": "N/A",
            "image": None,
            "streams": "N/A",
            "genres": "N/A"
        }

    return render_template('landing_page.html', auth_url=auth_url, artist_info=artist_info, song_info=song_info)

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
    chart = billboard.ChartData('hot-100')
    top_chart_songs = [{
        "rank": song.rank,
        "title": song.title,
        "artist": song.artist,
        "image": song.image,
        "weeks": song.weeks,
        "peak": song.peakPos
    } for song in chart[:10]]
    
    # Handle time range selection for Spotify top items (short_term, medium_term, long_term)
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
        recommended_music_posters = [get_song_album_cover_url(song, music[music['song'] == song]['artist'].values[0]) for song in recommendations]
        recommendations_with_posters = zip(recommendations, recommended_music_posters)

        # Default Spotify logo URL
        #default_spotify_logo_url = 'images/spotify-logo.png'

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

    return render_template('index.html', username=username, top_chart_songs=top_chart_songs, artists=top_artists, tracks=top_tracks, music_list=music_list, recommendations_with_posters=recommendations_with_posters, success_message=success_message)