# Legals Bot

Automated WordPress content pipeline for immigration law keywords. Reads keywords from Excel, generates SEO-optimised blog posts via Claude AI, publishes them to WordPress, and applies Yoast or Rank Math SEO meta — all hands-free.

---

## How it works

```
keywords.xlsx  →  Claude API  →  WordPress REST API  →  SEO meta patch
```

1. Reads each keyword from `keywords.xlsx`
2. Skips any keyword already in `processed_keywords.json`
3. Calls Claude to generate a full HTML blog post as structured JSON
4. Creates missing WordPress categories and tags automatically
5. Publishes the post (status configurable: `publish` or `draft`)
6. Patches Yoast SEO or Rank Math meta fields on the published post
7. Logs every step to the console and `bot.log`

---

## Prerequisites

- Python 3.10 or newer
- A WordPress site with:
  - The REST API enabled (default on all modern WP installs)
  - An **Application Password** generated for your user
  - Either the **Yoast SEO** or **Rank Math** plugin installed
- An **Anthropic API key** with access to `claude-sonnet-4-20250514`

---

## Installation

```bash
# 1. Clone or download the bot folder
cd "Legals bot"

# 2. (Recommended) create a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Configuration

### Step 1 — Create your `.env` file

Copy `.env.example` to `.env` and fill in your real credentials:

```
ANTHROPIC_API_KEY=sk-ant-...
WP_URL=https://yoursite.com
WP_USERNAME=your-wp-username
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

The `.env` file is loaded automatically at startup. Never commit it to source control.

#### How to generate a WordPress Application Password

1. Log in to WordPress admin
2. Go to **Users → Profile** (or **Users → All Users → Edit** for another user)
3. Scroll down to **Application Passwords**
4. Enter a name (e.g. `Legals Bot`) and click **Add New Application Password**
5. Copy the generated password — it looks like `xxxx xxxx xxxx xxxx xxxx xxxx`
6. Paste it as-is (spaces included) into `WP_APP_PASSWORD`

---

### Step 2 — Edit `config.py` for non-secret settings

Open [config.py](config.py) and adjust as needed:

| Setting | Default | Description |
|---|---|---|
| `EXCEL_FILE` | `keywords.xlsx` | Path to your keywords file |
| `KEYWORDS_COLUMN` | `Keywords` | Column header in the Excel sheet |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Claude model to use |
| `WP_POST_STATUS` | `publish` | Set to `draft` to review before publishing |
| `SEO_PLUGIN` | `yoast` | Set to `rankmath` for Rank Math |
| `DELAY_BETWEEN_POSTS` | `5` | Seconds to wait between keywords |

---

### Step 3 — Prepare `keywords.xlsx`

Create an Excel file named `keywords.xlsx` in the bot folder. It must have a column named **Keywords** (exact capitalisation):

| Keywords |
|---|
| hire emergency ice bond lawyer alabama retainer cost |
| immigration attorney consultation fee new york |
| deportation defense lawyer texas affordable |

Any other columns in the sheet are ignored.

---

## Running the bot

```bash
python main.py
```

The bot will process every keyword that is not already in `processed_keywords.json`. You can stop it at any time with `Ctrl+C` — completed keywords are saved immediately and will be skipped on the next run.

### Example console output

```
[INFO] 2025-01-15 10:22:01 — Legals Bot starting
[INFO] 2025-01-15 10:22:01 — Keywords total=35, already processed=0, pending=35
[INFO] 2025-01-15 10:22:01 — Processing keyword 1/35: hire emergency ice bond lawyer alabama retainer cost
[INFO] 2025-01-15 10:22:01 — Generating content with Claude...
[INFO] 2025-01-15 10:22:08 — Content generated: "How to Hire an Emergency ICE Bond Lawyer in Alabama..."
[INFO] 2025-01-15 10:22:08 — Resolving 2 categories...
[INFO] 2025-01-15 10:22:08 —   Creating category: Immigration Law
[INFO] 2025-01-15 10:22:09 —   Found existing category: Legal Help
[INFO] 2025-01-15 10:22:09 — Creating 12 tags...
[INFO] 2025-01-15 10:22:10 — Publishing post to WordPress...
[INFO] 2025-01-15 10:22:12 — Published: https://yoursite.com/hire-emergency-ice-bond-lawyer-alabama-retainer-cost
[INFO] 2025-01-15 10:22:12 — Setting Yoast SEO meta fields...
[INFO] 2025-01-15 10:22:12 — SEO optimized (post_id=1042).
[INFO] 2025-01-15 10:22:12 — SEO optimized. Moving to next keyword in 5s...
```

---

## Resuming after interruption

The bot is safe to stop and restart at any time. `processed_keywords.json` tracks every completed keyword:

```json
{
  "processed": ["keyword one", "keyword two"],
  "failed": ["keyword three"],
  "post_ids": {
    "keyword one": 123,
    "keyword two": 456
  }
}
```

On the next run the bot reads this file and skips anything in `processed`. Keywords in `failed` are retried automatically on the next run.

To reprocess a keyword that was already published, remove it from the `processed` list in `processed_keywords.json` and delete the corresponding WordPress post manually.

---

## Switching SEO plugin

**Yoast SEO** (default):
```python
# config.py
SEO_PLUGIN = "yoast"
```

**Rank Math**:
```python
# config.py
SEO_PLUGIN = "rankmath"
```

The bot writes the correct meta field names for whichever plugin is active.

---

## File reference

| File | Purpose |
|---|---|
| [main.py](main.py) | Orchestration loop |
| [config.py](config.py) | All settings |
| [excel_reader.py](excel_reader.py) | Reads keywords, manages the processed log |
| [claude_generator.py](claude_generator.py) | Calls Claude API, validates JSON response |
| [wordpress_poster.py](wordpress_poster.py) | Publishes posts, resolves categories & tags |
| [seo_optimizer.py](seo_optimizer.py) | Patches Yoast / Rank Math meta fields |
| [logger.py](logger.py) | Dual console + file logger |
| [keywords.xlsx](keywords.xlsx) | Your input keywords (you supply this) |
| [processed_keywords.json](processed_keywords.json) | Auto-maintained run log |
| [bot.log](bot.log) | Full debug log (created on first run) |
| [.env](.env) | Secret credentials (never commit) |
| [requirements.txt](requirements.txt) | Python dependencies |

---

## Troubleshooting

**`FileNotFoundError: keywords.xlsx not found`**
Place `keywords.xlsx` in the same folder as `main.py`.

**`ValueError: Column 'Keywords' not found`**
The column header in your Excel file must be exactly `Keywords` (capital K).

**`HTTP 401` from WordPress**
Check `WP_USERNAME` and `WP_APP_PASSWORD` in `.env`. Make sure the Application Password was generated for a user with permission to publish posts (Editor or Administrator role).

**`HTTP 403` on meta update**
WordPress restricts writing arbitrary meta via the REST API unless the meta key is registered. Make sure Yoast SEO or Rank Math is installed and active — they register their own meta keys.

**Claude returns invalid JSON**
This can happen if the model wraps its response in unexpected text. The bot logs the raw response to `bot.log` (DEBUG level) — check there for the full output. The keyword is marked as `failed` and retried on the next run.

**Rate limit errors from Anthropic**
Increase `DELAY_BETWEEN_POSTS` in `config.py`.
