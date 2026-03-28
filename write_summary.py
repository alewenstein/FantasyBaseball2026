"""
Generate a weekly summary using Claude.
"""

import os
import anthropic
from dotenv import load_dotenv

load_dotenv(override=True)


def build_results_text(results: dict) -> str:
    """Convert structured matchup data into plain text for the prompt."""
    lines = [f"Week {results['week']} Fantasy Baseball Matchup Results:\n"]
    for i, matchup in enumerate(results["matchups"], 1):
        if len(matchup) < 2:
            continue
        t1, t2 = matchup[0], matchup[1]
        s1 = f"{t1['score']:.2f}" if t1["score"] is not None else "N/A"
        s2 = f"{t2['score']:.2f}" if t2["score"] is not None else "N/A"
        winner = next((t for t in matchup if t["result"] == "win"), None)
        loser = next((t for t in matchup if t["result"] == "loss"), None)

        lines.append(f"Matchup {i}:")
        lines.append(f"  {t1['name']} (mgr: {t1['manager']}): {s1} pts")
        lines.append(f"  {t2['name']} (mgr: {t2['manager']}): {s2} pts")
        if winner and loser:
            lines.append(f"  Result: {winner['name']} defeats {loser['name']}")
        elif matchup[0]["result"] == "tie":
            lines.append("  Result: Tie")
        lines.append("")
    return "\n".join(lines)


def write_summary(results: dict) -> str:
    """Call Claude to write a factual weekly summary."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    results_text = build_results_text(results)

    prompt = f"""You are writing a weekly recap for a fantasy baseball league.
Write a concise, factual summary of the week's matchup results.
Keep it straightforward — who played who, who won, what the scores were.
No fluff, no jokes, no filler. Just the facts in plain readable sentences,
suitable for sending out to the league. One short paragraph per matchup.

{results_text}"""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text


if __name__ == "__main__":
    # Quick test with dummy data
    dummy = {
        "week": 1,
        "matchups": [
            [
                {"name": "Team A", "manager": "Alice", "score": 82.5, "result": "win"},
                {"name": "Team B", "manager": "Bob", "score": 74.1, "result": "loss"},
            ],
            [
                {"name": "Team C", "manager": "Carol", "score": 91.0, "result": "win"},
                {"name": "Team D", "manager": "Dave", "score": 68.3, "result": "loss"},
            ],
        ],
    }
    print(write_summary(dummy))
