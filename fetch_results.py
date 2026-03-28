"""
Fetch weekly matchup results from Yahoo Fantasy Baseball.
"""

import os
from dotenv import load_dotenv
from auth import get_query

load_dotenv(override=True)


def fetch_week(week: int) -> dict:
    """
    Pull all matchup data for the given week number.
    Returns a structured dict with matchup results.
    """
    query = get_query()

    print(f"Fetching matchups for week {week}...")
    matchups_raw = query.get_league_matchups_by_week(chosen_week=week)

    results = {
        "week": week,
        "matchups": [],
    }

    for matchup in matchups_raw:
        teams = matchup.teams

        # Each matchup has exactly 2 teams
        team_list = list(teams.values()) if isinstance(teams, dict) else teams

        team_data = []
        for team in team_list:
            t = {
                "name": str(team.name),
                "manager": _get_manager(team),
                "score": float(team.team_points.total) if hasattr(team, "team_points") else None,
                "win": bool(team.win_probability > 0.5) if hasattr(team, "win_probability") else None,
            }
            team_data.append(t)

        # Determine winner/loser by score if win flag not available
        if len(team_data) == 2 and team_data[0]["score"] is not None:
            if team_data[0]["score"] > team_data[1]["score"]:
                team_data[0]["result"] = "win"
                team_data[1]["result"] = "loss"
            elif team_data[1]["score"] > team_data[0]["score"]:
                team_data[1]["result"] = "win"
                team_data[0]["result"] = "loss"
            else:
                team_data[0]["result"] = "tie"
                team_data[1]["result"] = "tie"
        else:
            for t in team_data:
                t["result"] = "unknown"

        results["matchups"].append(team_data)

    return results


def _get_manager(team) -> str:
    """Extract manager name from team object."""
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


def print_results(results: dict):
    """Print a quick plaintext view of the week's results."""
    print(f"\n=== Week {results['week']} Results ===\n")
    for i, matchup in enumerate(results["matchups"], 1):
        if len(matchup) == 2:
            t1, t2 = matchup
            s1 = f"{t1['score']:.2f}" if t1["score"] is not None else "?"
            s2 = f"{t2['score']:.2f}" if t2["score"] is not None else "?"
            print(f"Matchup {i}: {t1['name']} ({s1}) vs {t2['name']} ({s2})")
            winner = next((t for t in matchup if t["result"] == "win"), None)
            if winner:
                print(f"  Winner: {winner['name']}")
        print()


if __name__ == "__main__":
    import sys

    week = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    results = fetch_week(week)
    print_results(results)
