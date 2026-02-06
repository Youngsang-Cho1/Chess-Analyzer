import requests
from typing import Optional, Dict, Any

class ChessComClient:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Chess Analyzer (Python)'
        }
        self.base_url = "https://api.chess.com/pub"

    def get_player_profile(self, username: str):
        url = f"{self.base_url}/player/{username}"
        try:
            res = requests.get(url, headers = self.headers)
            res.raise_for_status() # generate error if status code's 400 or 500 level
            return res.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching profile for {username}: {e}")
            return None

    def get_monthly_games(self, username: str, year: int, month: int):
        url = f"{self.base_url}/player/{username}/games/archives"
        year_month = f"{year}-{month:02d}"
        try:
            res = requests.get(url, headers = self.header)
            res.raise_for_status() 
            archives = res.json().get('archives', [])
            
            year_month_url = [archive for archive in archives if archive.endswith(year_month)][0]
            
            games_response = requests.get(year_month_url, headers=self.headers)
            games_response.raise_for_status()
            
            games = games_response.json().get('games', [])
            if not games:
                return None
            return games

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {year_month} games for {username}: {e}")
            return None

    def get_recent_games(self, username: str, limit: int = 10):
        archives_url = f"{self.base_url}/player/{username}/games/archives"
        try:
            res = requests.get(archives_url, headers = self.headers)
            res.raise_for_status()
            archives = res.json().get('archives', [])
            
            if not archives:
                return None

            last_month_url = archives[-1]
            games_response = requests.get(last_month_url, headers=self.headers)
            games_response.raise_for_status()
            
            games = games_response.json().get('games', [])
            if not games:
                return None
            
            games.reverse()
            return games[:limit]

        except requests.exceptions.RequestException as e:
            print(f"Error fetching games for {username}: {e}")
            return None
    
    def get_game_by_id(self, game_id: str):
        try:
            url = f"https://www.chess.com/callback/live/game/{game_id}"
            res = requests.get(url, headers=self.headers)
            res.raise_for_status()
            data = res.json()
            return data.get('game', {}).get('pgn')
        except Exception as e:
            print(f"Error fetching Game ID {game_id}: {e}")
            return None

    def get_latest_game_vs_player(self, username: str, opponent_username: str):
        try:
            archive_url = f"{self.base_url}/player/{username}/games/archives"
            res = requests.get(archive_url, headers=self.headers)
            res.raise_for_status()
            archives = res.json().get('archives', [])
            
            for archive_url in reversed(archives):
                games = requests.get(archive_url, headers=self.headers)
                games.raise_for_status()
                games = games.json().get('games', [])
                
                for game in games:
                    white = game.get('white', {}).get('username', '').lower()
                    black = game.get('black', {}).get('username', '').lower()
                    target = opponent_username.lower()
                    
                    if white == target or black == target:
                        return game.get('pgn')
            
            print(f"No game found against {opponent_username} in recent archive.")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching game vs {opponent_username}: {e}")
            return None
    