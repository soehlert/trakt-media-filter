import json
import os
import time

CONFIG_FILE = 'config.json'
TOKEN_FILE = 'trakt_token.json'

class ConfigManager:
    def __init__(self):
        self._config = self._load_json(CONFIG_FILE)
        self._tokens = self._load_json(TOKEN_FILE)

    def _load_json(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return {}

    def get_config(self, key):
        return self._config.get(key)

    def get_token(self, key):
        return self._tokens.get(key)

    def save_tokens(self, token_data):
        token_data['created_at'] = time.time()
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f)
        self._tokens = token_data  # Update the in-memory token data

    def refresh_needed(self):
        if 'expires_in' in self._tokens and 'created_at' in self._tokens:
            return time.time() > self._tokens['created_at'] + self._tokens['expires_in']
        return False

config_manager = ConfigManager()  # Create a global config manager instance
