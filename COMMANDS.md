# Legals Bot — Command Reference

## Sites
| Flag | Target Site |
|------|-------------|
| *(no flag)* | legal-counsel.net (default) |
| `--site american-counsel` | american-counsel.com |

---

## Main Commands

### `--run`
Generate content with Claude and post all pending keywords as drafts (includes categories + tags).

```powershell
py main.py --run
py main.py --run --site american-counsel
```

---

### `--draft-only`
Generate drafts only — skips categories and tags. Fastest option. Use `--set-categories-tags` later to add them.

```powershell
py main.py --draft-only
py main.py --draft-only --site american-counsel
```

---

### `--set-focus-keyword`
Set Rank Math focus keyword, SEO title, and meta description on all processed posts.

```powershell
py main.py --set-focus-keyword
py main.py --set-focus-keyword --site american-counsel
```

> **Requires:** Rank Math REST API must be enabled.
> WordPress Admin → Rank Math → General Settings → REST API → Enable "Add meta values in REST API responses"

---

### `--set-categories-tags`
Re-apply categories and tags to all processed posts. Safe to run multiple times (idempotent).

```powershell
py main.py --set-categories-tags
py main.py --set-categories-tags --site american-counsel
```

---

### `--publish`
Publish all draft posts. Skips any already published.

```powershell
py main.py --publish
py main.py --publish --site american-counsel
```

---

### `--full-pipeline`
Runs all four steps in sequence: generate drafts → set focus keywords → set categories/tags → publish.

```powershell
py main.py --full-pipeline
py main.py --full-pipeline --site american-counsel
```

---

## Modifier Flags

These can be combined with any main command above.

| Flag | Description | Example |
|------|-------------|---------|
| `-k "keyword"` | Process a single specific keyword | `py main.py --run -k "ice bond lawyer texas"` |
| `--limit N` | Process only the first N keywords | `py main.py --run --limit 5` |
| `--delay N` | Seconds between posts (default: 5) | `py main.py --publish --delay 10` |
| `--site NAME` | Target site: `legal-counsel` or `american-counsel` | `py main.py --run --site american-counsel` |

---

## Common Workflows

### Process one keyword as a test
```powershell
py main.py --run -k "hire emergency ice bond lawyer alabama retainer cost"
py main.py --run -k "hire emergency ice bond lawyer alabama retainer cost" --site american-counsel
```

### Process all keywords on both sites
```powershell
py main.py --run
py main.py --run --site american-counsel
```

### Publish one post as a test, then all
```powershell
py main.py --publish --limit 1
py main.py --publish
```

### Retry a failed keyword
Just re-run `--run` — the bot automatically skips processed keywords and retries failed ones.

```powershell
py main.py --run
```

### Full pipeline with slower pace
```powershell
py main.py --full-pipeline --delay 15
```

---

## State Files

| File | Purpose |
|------|---------|
| `processed_keywords.json` | Tracks processed/failed posts for legal-counsel.net |
| `processed_keywords_american-counsel.json` | Tracks processed/failed posts for american-counsel.com |
| `keywords.xlsx` | Source keyword list |
| `tags.txt` | 100 predefined tags applied to every post |
| `.env` | Credentials (API keys, WP passwords) |
