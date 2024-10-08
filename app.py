from flask import Flask, redirect, request, session, url_for
from views import views
from config import sp_oauth  # Import sp_oauth from config.py
import time

app = Flask(__name__)
app.secret_key = "random_secret_key"

app.register_blueprint(views, url_prefix='/view')

# Helper function to check if the token is expired and refresh it
def ensure_token_valid():
    token_info = session.get('token_info', None)

    if token_info is None:
        return False

    # Check if the token has expired
    now = int(time.time())
    is_token_expired = token_info['expires_at'] - now < 60  # Check if the token will expire in the next minute

    if is_token_expired:
        # If expired, refresh the token
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info  # Update the session with the new token

    return True

@app.route('/')
def home():
    return redirect(url_for('views.landing_page'))

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_cached_token()
    if not token_info:
        token_info = sp_oauth.get_access_token(code)

    # Store token in session
    session['token_info'] = token_info
    return redirect(url_for('views.show_top_items'))

@app.before_request
def refresh_token_if_needed():
    """Before each request, ensure the access token is valid."""
    if 'token_info' in session:
        ensure_token_valid()

if __name__ == '__main__':
    app.run(debug=True, port=5000)