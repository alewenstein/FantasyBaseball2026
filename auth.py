"""
Yahoo OAuth setup. Run this once to authenticate and save tokens.
After this you won't need to re-authenticate unless the token expires.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from yfpy.query import YahooFantasySportsQuery

load_dotenv(override=True)

ENV_DIR = Path(__file__).parent  # directory containing .env


def get_query() -> YahooFantasySportsQuery:
    """Return an authenticated query object. Call this from other scripts."""
    league_id = os.getenv("YAHOO_LEAGUE_ID")
    game_code = os.getenv("YAHOO_GAME_CODE", "mlb")
    # Yahoo game ID for MLB 2026 is 469 (not the year — Yahoo uses internal IDs)
    game_id_str = os.getenv("YAHOO_SEASON")
    game_id = int(game_id_str) if game_id_str else None  # None = auto-detect current season

    client_id = os.getenv("YAHOO_CLIENT_ID")
    client_secret = os.getenv("YAHOO_CLIENT_SECRET")

    query = YahooFantasySportsQuery(
        league_id=league_id,
        game_code=game_code,
        game_id=game_id,
        yahoo_consumer_key=client_id,
        yahoo_consumer_secret=client_secret,
        env_file_location=ENV_DIR,   # directory, not file path
        save_token_data_to_env_file=True,
        browser_callback=True,
    )
    return query


def setup_auth():
    league_id = os.getenv("YAHOO_LEAGUE_ID")
    client_id = os.getenv("YAHOO_CLIENT_ID")

    if not client_id or client_id == "your_client_id_here":
        print("ERROR: Set YAHOO_CLIENT_ID in your .env file first.")
        return None

    if not league_id or league_id == "your_league_id_here":
        print("ERROR: Set YAHOO_LEAGUE_ID in your .env file first.")
        print("Your league ID is in the URL: baseball.fantasysports.yahoo.com/b1/YOUR_ID")
        return None

    print("Opening browser for Yahoo authorization...")
    query = get_query()
    print("Auth set up successfully.")
    return query


if __name__ == "__main__":
    setup_auth()
