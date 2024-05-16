import requests
import webbrowser
import json
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# Load config file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)
CLIENT_ID = config['CLIENT_ID']
CLIENT_SECRET = config['CLIENT_SECRET']

REDIRECT_URI = 'http://localhost:8000'
API_BASE_URL = 'https://api.trakt.tv'
TOKEN_FILE = 'trakt_token.json'


class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'You can close this window now.')
        code = self.path.split('?code=')[1]
        self.server.access_code = code


def save_token(token_data):
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f)


def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    return None


def refresh_access_token(refresh_token):
    token_url = f"{API_BASE_URL}/oauth/token"
    payload = {
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'refresh_token'
    }
    response = requests.post(token_url, data=payload)
    token_data = response.json()
    save_token(token_data)
    return token_data['access_token']


def get_access_token():
    token_data = load_token()
    if token_data and 'access_token' in token_data:
        if 'expires_in' in token_data and time.time() < token_data['created_at'] + token_data['expires_in']:
            return token_data['access_token']
        elif 'refresh_token' in token_data:
            return refresh_access_token(token_data['refresh_token'])

    server_address = ('', 8000)
    httpd = HTTPServer(server_address, OAuthHandler)
    auth_url = f"{API_BASE_URL}/oauth/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    webbrowser.open(auth_url)
    httpd.handle_request()
    access_code = httpd.access_code
    httpd.server_close()
    token_url = f"{API_BASE_URL}/oauth/token"
    payload = {
        'code': access_code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    response = requests.post(token_url, data=payload)
    token_data = response.json()
    token_data['created_at'] = time.time()
    save_token(token_data)
    return token_data['access_token']


def search_movies(query, type='person'):
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': CLIENT_ID
    }
    search_url = f"{API_BASE_URL}/search/{type}?query={query}"
    response = requests.get(search_url, headers=headers)
    return response.json()


def mark_movie_as_watched(movie_id):
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': CLIENT_ID
    }
    watched_url = f"{API_BASE_URL}/sync/history"
    payload = {
        'movies': [{'ids': {'trakt': movie_id}}]
    }
    response = requests.post(watched_url, json=payload, headers=headers)
    return response.json()


if __name__ == "__main__":
    person_name = 'Tom Hanks'  # Example person for search
    movies_by_person = search_movies(person_name)
    print(movies_by_person)

    if movies_by_person and 'movie' in movies_by_person[0]:
        movie_id = movies_by_person[0]['movie']['ids']['trakt']
        watch_result = mark_movie_as_watched(movie_id)
        print(watch_result)
