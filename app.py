import os
import logging
from flask import Flask, redirect, request, session, url_for
from views import views
from config import sp_oauth  # Import sp_oauth from config.py
import time

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'random_secret_key')  # Use environment variable for secret key

# Configure logging
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
else:
    app.logger.setLevel(logging.INFO)

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
    app.logger.info('Home page accessed')
    return redirect(url_for('views.landing_page'))

@app.route('/callback')
def callback():
    app.logger.info('Callback route accessed')
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

@app.route('/healthz')
def health_check():
    # Basic health check - if the app is running, return 200 OK
    app.logger.info('Health check endpoint accessed')
    return '', 200

if __name__ == '__main__':
    # Uncomment the following line if you run the app directly (not through Gunicorn)
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))