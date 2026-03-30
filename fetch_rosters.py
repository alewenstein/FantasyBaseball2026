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


def _s(value) -> str:
    """Convert yfpy values to plain strings — handles bytes, str, and other types."""
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value) if value is not None else ""


def get_query() -> YahooFantasySportsQuery:
    """Return an authenticated query. Uses YAHOO_ACCESS_TOKEN_JSON in CI."""
    game_id_str = os.getenv("YAHOO_SEASON")
    token_json = os.getenv("YAHOO_ACCESS_TOKEN_JSON")  # full token blob (CI) or None (local)
    return YahooFantasySportsQuery(
        league_id=os.getenv("YAHOO_LEAGUE_ID"),
        game_code=os.getenv("YAHOO_GAME_CODE", "mlb"),
        game_id=int(game_id_str) if game_id_str else None,
        yahoo_consumer_key=None if token_json else os.getenv("YAHOO_CLIENT_ID"),
        yahoo_consumer_secret=None if token_json else os.getenv("YAHOO_CLIENT_SECRET"),
        yahoo_access_token_json=token_json,
        env_file_location=ENV_DIR,
        save_token_data_to_env_file=True,
        browser_callback=False,
    )


def fetch_rosters() -> dict:
    query = get_query()

    print("Fetching league teams...")
    teams_raw = query.get_league_teams()
    team_list = list(teams_raw.values()) if isinstance(teams_raw, dict) else teams_raw

    teams = []
    for team in team_list:
        team_id = int(team.team_id)
        team_name = _s(team.name)
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

    current_week, all_weeks = _fetch_all_weeks(query)

    # Keep legacy top-level matchups for backward compat (current week only)
    current_week_data = next((w for w in all_weeks if w["week"] == current_week), None)
    legacy_matchups = current_week_data["matchups"] if current_week_data else []

    return {
        "updated": datetime.now(timezone.utc).isoformat(),
        "current_week": current_week,
        "matchups": legacy_matchups,
        "all_weeks": all_weeks,
        "teams": teams,
    }


def _fetch_all_weeks(query):
    """Fetch matchups for every week of the season, with start/end dates."""
    current_week = None
    for method_name in ("get_league_metadata", "get_league_info"):
        try:
            meta = getattr(query, method_name)()
            current_week = int(meta.current_week)
            break
        except Exception:
            pass

    if current_week is None:
        print("  Could not auto-detect current week — skipping matchups.", file=sys.stderr)
        return None, []

    # Get date ranges for each week
    week_dates = {}
    try:
        game_weeks_raw = query.get_game_weeks()
        gw_list = list(game_weeks_raw.values()) if isinstance(game_weeks_raw, dict) else game_weeks_raw
        for gw in gw_list:
            try:
                wnum = int(gw.week)
                week_dates[wnum] = {
                    "start": str(gw.start)[:10],
                    "end":   str(gw.end)[:10],
                }
            except Exception:
                pass
        print(f"  Got date ranges for {len(week_dates)} weeks.")
    except Exception as e:
        print(f"  Warning: could not fetch game week dates: {e}", file=sys.stderr)

    total_weeks = max(week_dates.keys()) if week_dates else 25
    all_weeks = []

    for week in range(1, total_weeks + 1):
        print(f"  Fetching week {week} matchups...")
        try:
            matchups_raw = query.get_league_matchups_by_week(chosen_week=week)
            matchups = []
            week_start = None
            week_end = None
            for matchup in matchups_raw:
                teams = matchup.teams
                team_list = list(teams.values()) if isinstance(teams, dict) else teams
                if len(team_list) == 2:
                    matchups.append({
                        "team1_id": str(int(team_list[0].team_id)),
                        "team2_id": str(int(team_list[1].team_id)),
                    })
                if week_start is None:
                    try:
                        week_start = str(matchup.week_start)[:10]
                        week_end   = str(matchup.week_end)[:10]
                    except Exception:
                        pass
            entry = {"week": week, "matchups": matchups}
            if week_start:
                entry["start"] = week_start
                entry["end"]   = week_end
            elif week in week_dates:
                entry["start"] = week_dates[week]["start"]
                entry["end"]   = week_dates[week]["end"]
            all_weeks.append(entry)
        except Exception as e:
            print(f"  Warning: failed to fetch week {week}: {e}", file=sys.stderr)
            break

    return current_week, all_weeks


def _parse_roster(roster_raw) -> list:
    players = []
    items = list(roster_raw.values()) if isinstance(roster_raw, dict) else roster_raw

    for item in items:
        try:
            # yfpy sometimes nests the player under a roster-entry wrapper
            p = item.player if hasattr(item, "player") else item

            name = (
                _s(p.name.full)
                if hasattr(p, "name") and hasattr(p.name, "full")
                else _s(getattr(p, "name", "Unknown"))
            )
            mlb_team = _s(getattr(p, "editorial_team_abbr", "")).upper().strip()
            position = _s(getattr(p, "display_position", "")).strip()

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
            return _s(m.manager.nickname) if hasattr(m, "manager") else _s(m.nickname)
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
