import requests


class ChessComClient:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Chess Analyzer (Python)'
        }
        self.base_url = "https://api.chess.com/pub"

    def get_recent_games(self, username: str, limit: int = 10):
        """Walk monthly archives newest-first until we've collected at least
        `limit` games. Chess.com archives one URL per month — without this
        we'd cap at whatever fits in the most recent month."""
        archives_url = f"{self.base_url}/player/{username}/games/archives"
        try:
            res = requests.get(archives_url, headers=self.headers)
            res.raise_for_status()
            archives = res.json().get('archives', [])

            if not archives:
                return None

            collected = []
            # Newest month first; keep going until we have enough or run out.
            for month_url in reversed(archives):
                month_res = requests.get(month_url, headers=self.headers)
                month_res.raise_for_status()
                month_games = month_res.json().get('games', [])
                month_games.reverse()  # newest-first within the month
                collected.extend(month_games)
                if len(collected) >= limit:
                    break

            return collected or None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching games for {username}: {e}")
            return None
    
    def get_games_vs_opponent(self, username: str, opponent_username: str, limit: int = 5):
        collected_games = []
        try:
            archive_url = f"{self.base_url}/player/{username}/games/archives"
            res = requests.get(archive_url, headers=self.headers)
            res.raise_for_status()
            archives = res.json().get('archives', [])
            
            # Iterate archives in reverse (newest first)
            for archive_url in reversed(archives):
                if len(collected_games) >= limit:
                    break
                    
                try:
                    games_res = requests.get(archive_url, headers=self.headers)
                    games_res.raise_for_status()
                    games = games_res.json().get('games', [])
                    
                    # Process games in this archive (newest first within archive too)
                    for game in reversed(games):
                        white = game.get('white', {}).get('username', '').lower()
                        black = game.get('black', {}).get('username', '').lower()
                        target = opponent_username.lower()
                        
                        if white == target or black == target:
                            collected_games.append(game)
                            if len(collected_games) >= limit:
                                break
                except Exception as e:
                    print(f"Error fetching archive {archive_url}: {e}")
                    continue
            
            if not collected_games:
                print(f"No games found against {opponent_username}.")
                
            return collected_games
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching games vs {opponent_username}: {e}")
            return []
    