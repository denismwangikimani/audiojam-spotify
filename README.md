# AudioJam - Your Personalized Spotify Experience

AudioJam is a web application that enhances your Spotify experience by providing insights into your listening habits, personalized recommendations, and music discovery features. Built with Flask and the Spotify API, AudioJam offers a unique way to explore and interact with your music.

## Features

- **Spotify Integration**: Connect your Spotify account to see your top artists and tracks
- **Personalized Time Ranges**: View your music preferences over different time periods (short-term, medium-term, long-term)
- **Billboard Hot 100**: Stay updated with the latest trending songs on the Billboard charts
- **AI Music Taste Roast**: Get a humorous AI-generated roast of your music taste
- **Song Recommendations**: Discover new music based on your favorite songs
- **Playlist Creation**: Easily save your top tracks or recommendations to a Spotify playlist
- **Responsive Design**: Enjoy a seamless experience on desktop and mobile devices

## Tech Stack

- **Backend**: Python, Flask
- **APIs**: 
  - Spotify Web API (via spotipy)
  - Google Gemini API (for AI-based roasting)
  - Last.fm API (for artist information)
- **Frontend**: HTML, CSS
- **Data Analysis**: Scikit-learn (for recommendation system)
- **Web Scraping**: BeautifulSoup (for Billboard charts)
- **Deployment**: Render

## Setup and Installation

### Prerequisites

- Python 3.8+
- Spotify Developer Account
- Google Gemini API key
- Last.fm API key

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/audiojam-spotify.git
   cd audiojam-spotify
   ```

2. Set up a virtual environment:
    ```bash
    python -m venv audiojam-env
    source audiojam-env/bin/activate  # On Windows: audiojam-env\Scripts\activate
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Create a `.env` file in the project root with the following variables:
    ```
    SPOTIPY_CLIENT_ID=your_spotify_client_id
    SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
    SPOTIPY_REDIRECT_URI=http://localhost:5000/callback  # Or your deployed app's callback URL
    SECRET_KEY=your_flask_secret_key
    GEMINI_API_KEY=your_google_gemini_api_key
    LASTFM_API_KEY=your_last_fm_api_key
    ```

5. Run the application:
    ```bash
    python app.py
    ```

6. Access the application at [http://localhost:5000](http://localhost:5000)

## Deployment

The application is configured to be deployed on Render. The health check endpoint (`/healthz`) ensures that the app doesn't go to sleep on the free tier by allowing integration with uptime monitoring services like UptimeRobot.

## How It Works

- **Authentication**: Users authorize the app to access their Spotify data
- **Data Retrieval**: The app fetches user's top tracks, artists, and listening habits
- **Music Analysis**: AI analyzes music taste to generate personalized roasts
- **Recommendations**: The application uses similarity algorithms to suggest new music
- **Playlist Creation**: Users can save their discoveries directly to Spotify

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Spotify Web API
- Spotipy
- Billboard Charts
- Google Gemini API
- Flask
- BeautifulSoup
- Scikit-learn
- Render