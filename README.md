# Fantasy Baseball 2026 — Weekly Recap Tool

Pulls weekly matchup results from Yahoo Fantasy Baseball and writes a summary using Claude.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create a Yahoo Developer App

1. Go to https://developer.yahoo.com/apps/
2. Click **Create an App**
3. Fill in:
   - App name: anything (e.g. "Fantasy Baseball Recap")
   - App type: **Installed Application**
   - Description: anything
   - Redirect URI: `oob` (out of band — for local use)
   - API Permissions: check **Fantasy Sports** → Read
4. Submit and copy the **Client ID** and **Client Secret**

### 3. Find your League ID

Go to your league page on Yahoo Fantasy Baseball. The URL looks like:
```
https://baseball.fantasysports.yahoo.com/b1/123456
```
Your league ID is `123456`.

### 4. Configure credentials

```bash
cp .env.example .env
```

Edit `.env` and fill in:
- `YAHOO_CLIENT_ID`
- `YAHOO_CLIENT_SECRET`
- `YAHOO_LEAGUE_ID`
- `ANTHROPIC_API_KEY` (from https://console.anthropic.com/)

### 5. Authenticate with Yahoo (first time only)

```bash
python auth.py
```

This will open a browser window asking you to log in to Yahoo and authorize the app.
A `yahoo_tokens.json` file will be saved locally — keep it private.

## Usage

```bash
python main.py <week_number>
```

Example for week 5:
```bash
python main.py 5
```

This will:
1. Fetch all matchup results for that week
2. Print them to the terminal
3. Write a factual summary using Claude
4. Save the summary to `summary_week_5.txt`

Edit the text file however you want before sending it out to the league.
