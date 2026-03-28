"""
Fetch all team rosters from Yahoo Fantasy Baseball and save to docs/rosters.json.
Run by GitHub Actions daily to keep roster data fresh for the game-picker webpage.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from yfpy.query import YahooFantasySportsQuery

load_dotenv(override=True)

ENV_DIR = Path(__file__).parent


def get_query() -> YahooFantasySportsQuery:
    """Return an authenticated query. Uses refresh token in CI; no browser needed."""
    game_id_str = os.getenv("YAHOO_SEASON")
    return YahooFantasySportsQuery(
        league_id=os.getenv("YAHOO_LEAGUE_ID"),
        game_code=os.getenv("YAHOO_GAME_CODE", "mlb"),
        game_id=int(game_id_str) if game_id_str else None,
        yahoo_consumer_key=os.getenv("YAHOO_CLIENT_ID"),
        yahoo_consumer_secret=os.getenv("YAHOO_CLIENT_SECRET"),
        env_file_location=ENV_DIR,
        save_token_data_to_env_file=True,
        browser_callback=False,  # headless — relies on refresh token in .env
    )


def fetch_rosters() -> dict:
    query = get_query()

    print("Fetching league teams...")
    teams_raw = query.get_league_teams()
    team_list = list(teams_raw.values()) if isinstance(teams_raw, dict) else teams_raw

    teams = []
    for team in team_list:
        team_id = int(team.team_id)
        team_name = str(team.name)
        manager = _get_manager(team)

        print(f"  Fetching roster for {team_name} (id={team_id})...")
        try:
            roster_raw = query.get_team_roster_player_stats(team_id=team_id)
            players = _parse_roster(roster_raw)
        except Exception as e:
            print(f"  Warning: failed to fetch roster for {team_name}: {e}", file=sys.stderr)
            players = []

        teams.append({
            "team_id": str(team_id),
            "team_name": team_name,
            "manager": manager,
            "players": players,
        })

    return {
        "updated": datetime.now(timezone.utc).isoformat(),
        "teams": teams,
    }


def _parse_roster(roster_raw) -> list:
    players = []
    items = list(roster_raw.values()) if isinstance(roster_raw, dict) else roster_raw

    for item in items:
        try:
            # yfpy sometimes nests the player under a roster-entry wrapper
            p = item.player if hasattr(item, "player") else item

            name = (
                str(p.name.full)
                if hasattr(p, "name") and hasattr(p.name, "full")
                else str(getattr(p, "name", "Unknown"))
            )
            mlb_team = str(getattr(p, "editorial_team_abbr", "")).upper().strip()
            position = str(getattr(p, "display_position", "")).strip()

            if name and name != "Unknown":
                players.append({
                    "name": name,
                    "mlb_team": mlb_team,
                    "position": position,
                })
        except Exception as e:
            print(f"  Warning: could not parse player: {e}", file=sys.stderr)

    return players


def _get_manager(team) -> str:
    try:
        managers = team.managers
        if isinstance(managers, dict):
            managers = list(managers.values())
        if managers:
            m = managers[0]
            return str(m.manager.nickname) if hasattr(m, "manager") else str(m.nickname)
    except Exception:
        pass
    return "Unknown"


if __name__ == "__main__":
    data = fetch_rosters()

    out_path = Path(__file__).parent / "docs" / "rosters.json"
    out_path.parent.mkdir(exist_ok=True)

    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nSaved {len(data['teams'])} teams to {out_path}")
    print(f"Updated: {data['updated']}")
