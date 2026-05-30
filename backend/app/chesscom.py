import requests


class ChessComClient:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Chess Analyzer (Python)'
        }
        self.base_url = "https://api.chess.com/pub"

    def get_recent_games(self, username: str):
        """Yield games newest-first, walking monthly archives until exhausted."""
        archives_url = f"{self.base_url}/player/{username}/games/archives"
        try:
            res = requests.get(archives_url, headers=self.headers)
            res.raise_for_status()
            archives = res.json().get('archives', [])

            for month_url in reversed(archives):
                try:
                    month_res = requests.get(month_url, headers=self.headers)
                    month_res.raise_for_status()
                    month_games = month_res.json().get('games', [])
                    for game in reversed(month_games):
                        yield game
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching archive {month_url}: {e}")
                    continue

        except requests.exceptions.RequestException as e:
            print(f"Error fetching games for {username}: {e}")
    
    def get_games_vs_opponent(self, username: str, opponent_username: str):
        """Yield games vs opponent newest-first, walking monthly archives until exhausted."""
        target = opponent_username.lower()
        try:
            archive_url = f"{self.base_url}/player/{username}/games/archives"
            res = requests.get(archive_url, headers=self.headers)
            res.raise_for_status()
            archives = res.json().get('archives', [])

            for month_url in reversed(archives):
                try:
                    games_res = requests.get(month_url, headers=self.headers)
                    games_res.raise_for_status()
                    for game in reversed(games_res.json().get('games', [])):
                        white = game.get('white', {}).get('username', '').lower()
                        black = game.get('black', {}).get('username', '').lower()
                        if white == target or black == target:
                            yield game
                except Exception as e:
                    print(f"Error fetching archive {month_url}: {e}")
                    continue

        except requests.exceptions.RequestException as e:
            print(f"Error searching games vs {opponent_username}: {e}")
    