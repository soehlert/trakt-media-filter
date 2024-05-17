import requests
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from config import config_manager

API_BASE_URL = 'https://api.trakt.tv'
REDIRECT_URI = 'http://localhost:8000'


class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'You can close this window now.')
        code = self.path.split('?code=')[1]
        self.server.access_code = code


def get_access_token():
    if config_manager.get_token('access_token') and not config_manager.refresh_needed():
        return config_manager.get_token('access_token')

    if config_manager.refresh_needed() and config_manager.get_token('refresh_token'):
        return refresh_access_token(config_manager.get_token('refresh_token'))

    # If no valid token, initiate OAuth flow
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, OAuthHandler)
    client_id = config_manager.get_config('CLIENT_ID')
    client_secret = config_manager.get_config('CLIENT_SECRET')
    auth_url = f"{API_BASE_URL}/oauth/authorize?response_type=code&client_id={client_id}&redirect_uri={REDIRECT_URI}"
    webbrowser.open(auth_url)
    httpd.handle_request()
    access_code = httpd.access_code
    httpd.server_close()

    token_url = f"{API_BASE_URL}/oauth/token"
    payload = {
        'code': access_code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    response = requests.post(token_url, data=payload)
    config_manager.save_tokens(response.json())
    return response.json()['access_token']


def refresh_access_token(refresh_token):
    token_url = f"{API_BASE_URL}/oauth/token"
    payload = {
        'refresh_token': refresh_token,
        'client_id': config_manager.get_config('CLIENT_ID'),
        'client_secret': config_manager.get_config('CLIENT_SECRET'),
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'refresh_token'
    }
    response = requests.post(token_url, data=payload)
    config_manager.save_tokens(response.json())
    return response.json()['access_token']
