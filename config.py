import os
from dotenv import load_dotenv

load_dotenv()

# ── Excel ─────────────────────────────────────────────────────────────────────
EXCEL_FILE = "keywords.xlsx"
KEYWORDS_COLUMN = "Keywords"

# ── Anthropic ─────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your-anthropic-api-key-here")
CLAUDE_MODEL = "claude-sonnet-4-6"
# Posts are 2,400+ words with 20+ internal links — keep max_tokens high
CLAUDE_MAX_TOKENS = 16000

# ── Multi-site ────────────────────────────────────────────────────────────────
# Set SITE env var (or pass --site flag to main.py) to switch sites.
# "legal-counsel"    -> legal-counsel.net  (default)
# "american-counsel" -> american-counsel.com
# "greenafrica"      -> greenafrica.co.ke
# "elisamotors"      -> elisamotors.co.ke
SITE = os.getenv("SITE", "legal-counsel")

if SITE == "american-counsel":
    WP_URL          = os.getenv("WP_URL_2", "https://american-counsel.com")
    WP_USERNAME     = os.getenv("WP_USERNAME_2", "your-username")
    WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD_2", "xxxx xxxx xxxx xxxx xxxx xxxx")
    CTA_EMAIL       = os.getenv("CTA_EMAIL_2", "support@american-counsel.com")
    PROCESSED_LOG   = "processed_keywords_american-counsel.json"
elif SITE == "greenafrica":
    WP_URL          = os.getenv("WP_URL_3", "https://greenafrica.co.ke")
    WP_USERNAME     = os.getenv("WP_USERNAME_3", "your-username")
    WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD_3", "xxxx xxxx xxxx xxxx xxxx xxxx")
    CTA_EMAIL       = os.getenv("CTA_EMAIL_3", "support@greenafrica.co.ke")
    PROCESSED_LOG   = "processed_keywords_greenafrica.json"
elif SITE == "elisamotors":
    WP_URL          = os.getenv("WP_URL_4", "https://elisamotors.co.ke")
    WP_USERNAME     = os.getenv("WP_USERNAME_4", "your-username")
    WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD_4", "xxxx xxxx xxxx xxxx xxxx xxxx")
    CTA_EMAIL       = os.getenv("CTA_EMAIL_4", "info@elisamotors.co.ke")
    PROCESSED_LOG   = "processed_keywords_elisamotors.json"
else:
    WP_URL          = os.getenv("WP_URL", "https://yoursite.com")
    WP_USERNAME     = os.getenv("WP_USERNAME", "your-username")
    WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "xxxx xxxx xxxx xxxx xxxx xxxx")
    CTA_EMAIL       = "support@legal-councel.net"
    PROCESSED_LOG   = "processed_keywords.json"

# ── WordPress ─────────────────────────────────────────────────────────────────
WP_POST_STATUS = "draft"     # "publish" | "draft"

# ── SEO Plugin ────────────────────────────────────────────────────────────────
# "yoast" | "rankmath"
SEO_PLUGIN = "yoast"

# ── Rate limiting ─────────────────────────────────────────────────────────────
DELAY_BETWEEN_POSTS = 5   # seconds
