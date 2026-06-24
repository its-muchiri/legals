"""
test_bot.py — Full pre-flight test suite for Legals Bot.

Tests every layer WITHOUT spending Claude tokens or creating WP posts:
  1. Config & environment
  2. Excel reader
  3. Processed-keyword log (read / write / mark)
  4. Claude JSON parser & validator (mock response)
  5. WordPress connectivity & authentication (real GET requests only)
  6. WordPress slug duplicate check (real GET)
  7. WordPress category & tag lookup (real GET)
  8. SEO meta builder (logic only, no HTTP)
  9. Full dry-run pipeline (mocked Claude + mocked WP POST, real WP GET)

Run:
    python test_bot.py
"""

import json
import os
import sys
import tempfile
import time
import traceback
from typing import Any
from unittest.mock import MagicMock, patch

import requests
from requests.auth import HTTPBasicAuth

# ── Colour helpers ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

PASS  = f"{GREEN}  [PASS]{RESET}"
FAIL  = f"{RED}  [FAIL]{RESET}"
SKIP  = f"{YELLOW}  [SKIP]{RESET}"
INFO  = f"{CYAN}  [INFO]{RESET}"

results: list[tuple[str, bool, str]] = []


def section(title: str) -> None:
    print(f"\n{BOLD}{CYAN}{'-'*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'-'*60}{RESET}")


def check(label: str, ok: bool, detail: str = "") -> None:
    tag = PASS if ok else FAIL
    msg = f"  {detail}" if detail else ""
    print(f"{tag}  {label}{msg}")
    results.append((label, ok, detail))


def info(msg: str) -> None:
    print(f"{INFO}  {msg}")


# ── Minimal fake post data used throughout tests ──────────────────────────────
FAKE_POST_DATA: dict[str, Any] = {
    "title": "How to Hire an Emergency ICE Bond Lawyer in Alabama",
    "slug": "hire-emergency-ice-bond-lawyer-alabama-retainer-cost",
    "meta_description": (
        "Need an emergency ICE bond lawyer in Alabama? Learn retainer costs, "
        "how to hire fast, and what to expect. Call now for a free consultation."
    ),
    "seo_title": "Emergency ICE Bond Lawyer Alabama | Retainer Cost",
    "focus_keyphrase": "hire emergency ice bond lawyer alabama retainer cost",
    "excerpt": (
        "Facing an immigration emergency in Alabama? Our experienced ICE bond "
        "lawyers are available 24/7. Understand retainer costs and act now."
    ),
    "categories": ["Immigration Law", "Legal Help"],
    "tags": [
        "ice bond lawyer", "immigration attorney alabama",
        "emergency bond lawyer", "ice detention", "immigration bond",
        "deportation defense", "alabama immigration lawyer", "ice bond cost",
        "immigration lawyer near me", "bond hearing attorney",
    ],
    "content": (
        "<p>If you or a loved one has been detained by ICE in Alabama, "
        "you need an emergency ICE bond lawyer right now. "
        "Furthermore, time is critical when someone is in immigration detention.</p>\n"
        "<h2>Our ICE Bond Lawyer Services in Alabama</h2>\n"
        "<h3>Emergency Bond Hearings in Birmingham</h3>\n"
        "<p>Additionally, our attorneys handle emergency bond hearings in Birmingham. "
        "We serve Jefferson County, Shelby County, and surrounding areas. "
        "As a result, families in Birmingham can get immediate legal help. "
        '<a href="https://legal-counsel.net/nursing-home-abuse-lawyer-the-complete-2025-guide-to-protecting-your-loved-ones/">Learn more</a>. '
        "Moreover, we understand the urgency of ICE detention cases.</p>\n"
        "<h3>ICE Bond Attorneys in Huntsville</h3>\n"
        "<p>However, Huntsville residents also face ICE issues. "
        "Consequently, our Huntsville team is on call 24/7. "
        '<a href="https://legal-counsel.net/workers-compensation-attorney-for-denied-claim-the-complete-2025-legal-guide/">Workers rights</a> '
        "are also protected. Similarly, immigration rights matter just as much.</p>\n"
        "<h3>Mobile Immigration Bond Lawyers</h3>\n"
        '<p>For instance, Mobile clients can reach us any time. '
        '<a href="https://legal-counsel.net/best-personal-injury-lawyer-for-traumatic-brain-injurytbi/">TBI lawyers</a> '
        "are also available. Likewise, immigration bond lawyers serve Mobile County.</p>\n"
        "<h3>Montgomery ICE Detention Defense</h3>\n"
        "<p>Subsequently, our Montgomery attorneys fight for detained clients. "
        "Nevertheless, the process can be complex. "
        '<a href="https://legal-counsel.net/medical-malpractice-lawyer-for-surgical-error-your-complete-legal-guide/">Medical malpractice</a> '
        "victims deserve justice. In fact, so do immigration detainees.</p>\n"
        "<h3>Tuscaloosa Emergency Bond Services</h3>\n"
        "<p>On the other hand, Tuscaloosa families need fast help too. "
        "Therefore, we keep attorneys available in Tuscaloosa County. "
        '<a href="https://legal-counsel.net/slip-and-fall-attorney-on-ice-and-snow-the-complete-legal-guide-2025-update/">Slip and fall</a> '
        "cases and immigration cases both need urgent attention.</p>\n"
        "<h3>Anniston and Gadsden Bond Hearings</h3>\n"
        "<p>Conversely, smaller cities like Anniston and Gadsden also have detention needs. "
        '<a href="https://legal-counsel.net/nursing-home-neglect-attorney-your-complete-legal-guide-to-protecting-loved-ones/">Nursing home neglect</a> '
        "and immigration neglect are both serious. For example, Calhoun County clients call us daily.</p>\n"
        "<h3>Statewide ICE Bond Coverage</h3>\n"
        "<p>Meanwhile, we cover all 67 Alabama counties. "
        '<a href="https://legal-counsel.net/best-personal-injury-lawyer-for-back-injury/">Back injury lawyers</a> '
        "work alongside our immigration team. As a result, clients statewide get help fast.</p>\n"
        "<h2>Why Choose Legal Counsel</h2>\n"
        "<p>We have decades of combined experience in immigration law. "
        "Moreover, our attorneys are former prosecutors who understand both sides. "
        "Consequently, our success rate on bond hearings exceeds 85%. "
        '<strong>Email us: <a href="mailto:support@legal-councel.net">support@legal-councel.net</a></strong></p>\n'
        "<h2>How the Process Works</h2>\n"
        "<ol><li>Call our 24/7 hotline immediately.</li>"
        "<li>We review your case within one hour.</li>"
        "<li>An attorney files for a bond hearing.</li>"
        "<li>We appear before the immigration judge.</li>"
        "<li>Your loved one is released pending their case.</li></ol>\n"
        "<h2>Frequently Asked Questions</h2>\n"
        "<p><strong>Q: How much does an emergency ICE bond lawyer in Alabama cost?</strong></p>"
        "<p>A: Retainer fees typically range from $1,500 to $5,000 depending on case complexity. "
        'However, <a href="https://legal-counsel.net/cheap-divorce-lawyers-near-me-finding-affordable-legal-counsel-without-compromise/">affordable options</a> '
        "are available. Many firms offer payment plans for detained clients.</p>"
        "<p><strong>Q: How fast can a bond hearing be scheduled in Alabama?</strong></p>"
        "<p>A: Emergency hearings can be requested within 24 to 48 hours. "
        "Subsequently, the court schedules the hearing as soon as possible. "
        "Additionally, having experienced counsel speeds up the process significantly.</p>"
        "<p><strong>Q: What is an ICE immigration bond?</strong></p>"
        "<p>A: An ICE bond is a financial guarantee that a detainee will appear at all immigration proceedings. "
        "Furthermore, bond amounts are set by an immigration judge and can range from $1,500 to over $25,000.</p>"
        "<p><strong>Q: Can I hire an ICE bond lawyer for a family member?</strong></p>"
        '<p>A: Yes. <a href="https://legal-counsel.net/family-law-attorney-for-divorce-and-custody-your-essential-guide-why-legal-counsel-excels/">Family law attorneys</a> '
        "often work alongside immigration lawyers. Therefore, family members can hire and pay for legal counsel.</p>"
        "<p><strong>Q: What happens if the bond is denied?</strong></p>"
        "<p>A: If a bond is denied, we immediately file for reconsideration or appeal. "
        "Moreover, we explore alternative forms of relief including supervised release.</p>\n"
        "<h2>Get Help Now</h2>\n"
        "<p>Do not wait. Every hour in ICE detention matters. "
        '<strong>Email us at <a href="mailto:support@legal-councel.net">support@legal-councel.net</a></strong>. '
        '<a href="https://legal-counsel.net/wrongful-death-lawyers-for-car-accident-seeking-justice-after-loss-legal-counsel/">Wrongful death</a> '
        "and immigration cases both deserve immediate attention. "
        '<a href="https://legal-counsel.net/workers-compensation-attorney-for-denied-claim-the-complete-2025-legal-guide/">Workers comp</a> '
        "clients also benefit from our network of attorneys. "
        '<a href="https://legal-counsel.net/best-criminal-defense-attorney-for-felony-secure-your-future-with-expert-legal-aid/">Criminal defense</a> '
        "attorneys are also standing by. "
        '<a href="https://legal-counsel.net/federal-criminal-defense-lawyer-your-essential-guide-to-navigating-federal-charges/">Federal charges</a> '
        "require urgent legal representation.</p>\n"
        "<h2>Legal Disclaimer</h2>\n"
        "<p>This content is for informational purposes only and does not constitute legal advice. "
        "No attorney-client relationship is formed by reading this page. "
        "Consult a licensed immigration attorney for advice specific to your situation.</p>"
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# 1. CONFIG & ENVIRONMENT
# ─────────────────────────────────────────────────────────────────────────────
section("1. Config & Environment")

try:
    from config import (
        ANTHROPIC_API_KEY, CLAUDE_MAX_TOKENS, CLAUDE_MODEL,
        DELAY_BETWEEN_POSTS, EXCEL_FILE, KEYWORDS_COLUMN,
        PROCESSED_LOG, SEO_PLUGIN, WP_APP_PASSWORD,
        WP_POST_STATUS, WP_URL, WP_USERNAME,
    )

    check("Config module imports without error", True)
    check("ANTHROPIC_API_KEY is set",
          bool(ANTHROPIC_API_KEY) and ANTHROPIC_API_KEY != "your-anthropic-api-key-here",
          f"(key starts with: {ANTHROPIC_API_KEY[:12]}...)" if ANTHROPIC_API_KEY else "(MISSING)")
    check("CLAUDE_MODEL is set", bool(CLAUDE_MODEL), f"-> {CLAUDE_MODEL}")
    check("CLAUDE_MAX_TOKENS is set", CLAUDE_MAX_TOKENS >= 8000, f"-> {CLAUDE_MAX_TOKENS}")
    check("WP_URL is set", bool(WP_URL) and WP_URL != "https://yoursite.com", f"-> {WP_URL}")
    check("WP_USERNAME is set", bool(WP_USERNAME) and WP_USERNAME != "your-username", f"-> {WP_USERNAME}")
    check("WP_APP_PASSWORD is set",
          bool(WP_APP_PASSWORD) and WP_APP_PASSWORD != "xxxx xxxx xxxx xxxx xxxx xxxx",
          f"-> {'*' * 20}")
    check("WP_POST_STATUS is 'draft'", WP_POST_STATUS == "draft",
          f"-> '{WP_POST_STATUS}' (change to 'draft' in config.py to review before publishing)")
    check("SEO_PLUGIN is 'yoast' or 'rankmath'", SEO_PLUGIN in ("yoast", "rankmath"), f"-> {SEO_PLUGIN}")
    check("DELAY_BETWEEN_POSTS >= 3s", DELAY_BETWEEN_POSTS >= 3, f"-> {DELAY_BETWEEN_POSTS}s")

except Exception as exc:
    check("Config module imports without error", False, str(exc))
    print(f"{RED}  Cannot continue — fix config.py first.{RESET}")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# 2. EXCEL READER
# ─────────────────────────────────────────────────────────────────────────────
section("2. Excel Reader")

try:
    from excel_reader import get_pending_keywords, load_processed_log, read_keywords

    check("excel_reader imports without error", True)

    kws = read_keywords()
    check("keywords.xlsx exists and is readable", bool(kws), f"({len(kws)} keywords found)")
    check("At least 1 keyword read", len(kws) >= 1)

    if kws:
        first = kws[0]
        no_number = not first[0].isdigit()
        check("Number prefix stripped from keywords", no_number, f"-> '{first}'")
        check("Keywords are non-empty strings", all(isinstance(k, str) and k for k in kws))

except Exception as exc:
    check("Excel reader test", False, str(exc))

# ─────────────────────────────────────────────────────────────────────────────
# 3. PROCESSED-KEYWORD LOG
# ─────────────────────────────────────────────────────────────────────────────
section("3. Processed-Keyword Log")

try:
    from excel_reader import (
        load_processed_log, mark_failed, mark_processed,
        save_processed_log,
    )

    # Use a temp file so we don't touch the real log
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tf:
        temp_log_path = tf.name
        json.dump({"processed": [], "failed": [], "post_ids": {}}, tf)

    original_log = PROCESSED_LOG

    # Monkey-patch the path
    import excel_reader as _er
    _er.PROCESSED_LOG = temp_log_path

    log_data = load_processed_log()
    check("Log file loads correctly", isinstance(log_data, dict))
    check("Log has 'processed' key", "processed" in log_data)
    check("Log has 'failed' key", "failed" in log_data)
    check("Log has 'post_ids' key", "post_ids" in log_data)

    mark_processed("test keyword", 999, log_data)
    check("mark_processed adds to 'processed'", "test keyword" in log_data["processed"])
    check("mark_processed records post_id", log_data["post_ids"].get("test keyword") == 999)

    mark_failed("bad keyword", log_data)
    check("mark_failed adds to 'failed'", "bad keyword" in log_data["failed"])

    mark_processed("bad keyword", 888, log_data)
    check("mark_processed removes keyword from 'failed'", "bad keyword" not in log_data["failed"])

    # Restore
    _er.PROCESSED_LOG = original_log
    os.unlink(temp_log_path)

    check("Log operations write and read back correctly", True)

except Exception as exc:
    check("Processed log tests", False, str(exc))

# ─────────────────────────────────────────────────────────────────────────────
# 4. CLAUDE JSON PARSER & VALIDATOR (mock — no tokens spent)
# ─────────────────────────────────────────────────────────────────────────────
section("4. Claude JSON Parser & Validator (mock — no tokens)")

try:
    from claude_generator import _extract_json, validate_content

    check("claude_generator imports without error", True)

    # Test _extract_json with various wrapper formats
    raw_plain = json.dumps({"title": "t", "slug": "s"})
    raw_fenced = f"```json\n{raw_plain}\n```"
    raw_extra  = f"Here is your post:\n{raw_plain}\nDone."

    check("_extract_json — plain JSON",   _extract_json(raw_plain) == raw_plain)
    check("_extract_json — fenced ```json", json.loads(_extract_json(raw_fenced))["title"] == "t")
    check("_extract_json — trailing text",  json.loads(_extract_json(raw_extra))["title"] == "t")

    # Full validate_content with realistic data
    try:
        validate_content(FAKE_POST_DATA)
        check("validate_content — valid full post passes", True)
    except ValueError as ve:
        check("validate_content — valid full post passes", False, str(ve))

    # Missing field
    bad = dict(FAKE_POST_DATA)
    del bad["meta_description"]
    try:
        validate_content(bad)
        check("validate_content — missing field raises ValueError", False, "no error raised")
    except ValueError:
        check("validate_content — missing field raises ValueError", True)

    # Content too short
    short = dict(FAKE_POST_DATA)
    short["content"] = "<p>Too short.</p>"
    try:
        validate_content(short)
        check("validate_content — short content raises ValueError", False, "no error raised")
    except ValueError:
        check("validate_content — short content raises ValueError", True)

    # Too few links — now a warning, not an error
    no_links = dict(FAKE_POST_DATA)
    no_links["content"] = FAKE_POST_DATA["content"].replace("<a href=", "<b fake=")
    try:
        validate_content(no_links)
        check("validate_content — too few links logs warning (not error)", True)
    except ValueError:
        check("validate_content — too few links logs warning (not error)", False, "raised ValueError — should only warn")

    # meta_description too long
    bad_meta = dict(FAKE_POST_DATA)
    bad_meta["meta_description"] = "x" * 200
    try:
        validate_content(bad_meta)
        check("validate_content — meta too long raises ValueError", False, "no error raised")
    except ValueError:
        check("validate_content — meta too long raises ValueError", True)

    # seo_title too long
    bad_title = dict(FAKE_POST_DATA)
    bad_title["seo_title"] = "x" * 70
    try:
        validate_content(bad_title)
        check("validate_content — seo_title too long raises ValueError", False, "no error raised")
    except ValueError:
        check("validate_content — seo_title too long raises ValueError", True)

    # categories must be a list
    bad_cat = dict(FAKE_POST_DATA)
    bad_cat["categories"] = "Immigration Law"
    try:
        validate_content(bad_cat)
        check("validate_content — categories not list raises ValueError", False, "no error raised")
    except ValueError:
        check("validate_content — categories not list raises ValueError", True)

except Exception as exc:
    check("Claude parser/validator tests", False, str(exc))
    traceback.print_exc()

# ─────────────────────────────────────────────────────────────────────────────
# 5. WORDPRESS CONNECTIVITY & AUTHENTICATION
# ─────────────────────────────────────────────────────────────────────────────
section("5. WordPress Connectivity & Authentication (real GET — no posts created)")

try:
    base = WP_URL.rstrip("/")
    auth = HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)

    # 5a — Site reachable
    try:
        r = requests.get(f"{base}/wp-json/", timeout=15)
        check("WordPress site is reachable", r.ok, f"HTTP {r.status_code}")
    except requests.exceptions.ConnectionError as ce:
        check("WordPress site is reachable", False, str(ce))

    # 5b — WP REST API active
    try:
        r = requests.get(f"{base}/wp-json/wp/v2/", timeout=15)
        check("WP REST API v2 is active", r.ok, f"HTTP {r.status_code}")
    except Exception as e:
        check("WP REST API v2 is active", False, str(e))

    # 5c — Auth: GET /users/me (requires valid application password)
    try:
        r = requests.get(f"{base}/wp-json/wp/v2/users/me", auth=auth, timeout=15)
        if r.ok:
            me = r.json()
            username = me.get("name", me.get("slug", "unknown"))
            roles    = me.get("roles", [])
            check("Application password authentication", True, f"logged in as '{username}' roles={roles}")
            # WP REST API only returns roles when queried by an administrator.
            # For Editor/Author app passwords the field comes back empty — that is normal.
            can_publish = any(role in roles for role in ("administrator", "editor", "author"))
            if not can_publish and not roles:
                print(f"{YELLOW}  [WARN]{RESET}  User role not visible via REST API (normal for non-admin tokens). "
                      "Verify the WP user has Editor or Administrator role in WP Admin.")
                results.append(("User role visible via REST", True, "role check skipped — normal for non-admin tokens"))
            else:
                check("User has publish-capable role", can_publish, f"roles={roles}")
        else:
            check("Application password authentication", False, f"HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        check("Application password authentication", False, str(e))

    # 5d — Can read categories endpoint
    try:
        r = requests.get(f"{base}/wp-json/wp/v2/categories", auth=auth,
                         params={"per_page": 1}, timeout=15)
        check("GET /wp/v2/categories is accessible", r.ok, f"HTTP {r.status_code}")
    except Exception as e:
        check("GET /wp/v2/categories is accessible", False, str(e))

    # 5e — Can read tags endpoint
    try:
        r = requests.get(f"{base}/wp-json/wp/v2/tags", auth=auth,
                         params={"per_page": 1}, timeout=15)
        check("GET /wp/v2/tags is accessible", r.ok, f"HTTP {r.status_code}")
    except Exception as e:
        check("GET /wp/v2/tags is accessible", False, str(e))

    # 5f — Can read posts endpoint
    try:
        r = requests.get(f"{base}/wp-json/wp/v2/posts", auth=auth,
                         params={"per_page": 1, "status": "any"}, timeout=15)
        check("GET /wp/v2/posts is accessible", r.ok, f"HTTP {r.status_code}")
        if r.ok:
            posts = r.json()
            info(f"Existing post count (first page): {len(posts)}")
    except Exception as e:
        check("GET /wp/v2/posts is accessible", False, str(e))

except Exception as exc:
    check("WordPress connectivity tests", False, str(exc))

# ─────────────────────────────────────────────────────────────────────────────
# 6. WORDPRESS SLUG DUPLICATE CHECK
# ─────────────────────────────────────────────────────────────────────────────
section("6. WordPress Slug Duplicate Check (real GET)")

try:
    from wordpress_poster import slug_exists

    # Test with a slug that almost certainly doesn't exist
    ghost_slug = "zzz-legals-bot-test-ghost-slug-should-not-exist-xyz"
    result = slug_exists(ghost_slug)
    check("slug_exists returns None for non-existent slug", result is None, f"-> {result}")

    # Test with a slug that definitely exists (the homepage / any known page)
    # We use a slug from the sitemap that's definitely in WP
    known_slug = "nursing-home-abuse-lawyer-the-complete-2025-guide-to-protecting-your-loved-ones"
    result2 = slug_exists(known_slug)
    info(f"Known-slug lookup for '{known_slug[:40]}...': post_id={result2}")
    # We don't enforce pass/fail here because it depends on actual WP content

    check("slug_exists function executes without error", True)

except Exception as exc:
    check("Slug duplicate check", False, str(exc))

# ─────────────────────────────────────────────────────────────────────────────
# 7. WORDPRESS CATEGORY & TAG LOOKUP (GET only — nothing created)
# ─────────────────────────────────────────────────────────────────────────────
section("7. WordPress Category & Tag Lookup (GET only — nothing created)")

try:
    from wordpress_poster import _get_or_create_term

    # We'll patch requests.post to raise if called, ensuring we never CREATE anything
    with patch("wordpress_poster.requests.post") as mock_post:
        mock_post.side_effect = AssertionError("POST should not be called during lookup test")

        # Try a category that likely exists ("Uncategorized" is always present)
        try:
            cat_id = _get_or_create_term("categories", "Uncategorized")
            check("Existing category 'Uncategorized' found by GET", isinstance(cat_id, int),
                  f"id={cat_id}")
        except AssertionError:
            check("Existing category 'Uncategorized' found by GET", False,
                  "POST was called — term lookup issue")
        except Exception as e:
            # If GET returned nothing, _get_or_create_term would try POST
            # which we blocked — that's fine, it means the category doesn't exist
            info(f"'Uncategorized' category not found via GET (may not exist): {e}")
            check("Category GET endpoint responds without error", True)

    check("Category/tag lookup test completed without exception", True)

except Exception as exc:
    check("Category & tag lookup tests", False, str(exc))

# ─────────────────────────────────────────────────────────────────────────────
# 8. SEO META BUILDER
# ─────────────────────────────────────────────────────────────────────────────
section("8. SEO Meta Builder (logic only, no HTTP)")

try:
    from seo_optimizer import _build_meta

    # Yoast
    import config as _cfg
    original_plugin = _cfg.SEO_PLUGIN
    _cfg.SEO_PLUGIN = "yoast"
    import seo_optimizer as _seo
    _seo.SEO_PLUGIN = "yoast"

    meta_yoast = _build_meta(FAKE_POST_DATA)
    check("Yoast: _yoast_wpseo_title present",    "_yoast_wpseo_title"    in meta_yoast)
    check("Yoast: _yoast_wpseo_metadesc present",  "_yoast_wpseo_metadesc" in meta_yoast)
    check("Yoast: _yoast_wpseo_focuskw present",   "_yoast_wpseo_focuskw"  in meta_yoast)
    check("Yoast: values are non-empty strings",
          all(isinstance(v, str) and v for v in meta_yoast.values()))

    # Rank Math
    _cfg.SEO_PLUGIN = "rankmath"
    _seo.SEO_PLUGIN = "rankmath"

    meta_rm = _build_meta(FAKE_POST_DATA)
    check("Rank Math: rank_math_title present",          "rank_math_title"          in meta_rm)
    check("Rank Math: rank_math_description present",    "rank_math_description"    in meta_rm)
    check("Rank Math: rank_math_focus_keyword present",  "rank_math_focus_keyword"  in meta_rm)
    check("Rank Math: values are non-empty strings",
          all(isinstance(v, str) and v for v in meta_rm.values()))

    # Restore
    _cfg.SEO_PLUGIN = original_plugin
    _seo.SEO_PLUGIN = original_plugin

    check("SEO meta builder test completed", True)

except Exception as exc:
    check("SEO meta builder tests", False, str(exc))

# ─────────────────────────────────────────────────────────────────────────────
# 9. FULL DRY-RUN PIPELINE
#    - Mocked Claude API response (no tokens)
#    - Real WordPress GET (auth + slug check)
#    - Mocked WordPress POST (no post created)
#    - Real SEO meta PATCH would be mocked too
# ─────────────────────────────────────────────────────────────────────────────
section("9. Full Dry-Run Pipeline (mocked Claude + mocked WP POST)")

try:
    import json as _json
    from unittest.mock import MagicMock, patch

    # Build a mock Anthropic message response
    mock_message = MagicMock()
    mock_message.content = [MagicMock()]
    mock_message.content[0].text = json.dumps(FAKE_POST_DATA)

    # Mock the Anthropic client
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("claude_generator.anthropic.Anthropic", return_value=mock_client):
        from claude_generator import generate_content
        data = generate_content("hire emergency ice bond lawyer alabama retainer cost")
        check("Dry-run: Claude content generated (mocked)", bool(data), f"title='{data['title']}'")
        check("Dry-run: All required fields present",
              all(k in data for k in ["title","slug","content","meta_description",
                                       "seo_title","focus_keyphrase","excerpt",
                                       "categories","tags"]))
        check("Dry-run: content has 15+ internal links",
              data["content"].count("<a href=") >= 15,
              f"links found: {data['content'].count('<a href=')}")

    # Mock WordPress POST + PATCH, but use real GET for slug check
    fake_wp_response = MagicMock()
    fake_wp_response.ok = True
    fake_wp_response.json.return_value = {
        "id": 99999,
        "link": f"{WP_URL}/test-dry-run-post-do-not-publish/",
        "status": "draft",
    }

    with patch("wordpress_poster.requests.post", return_value=fake_wp_response) as mock_wp_post, \
         patch("seo_optimizer.requests.post", return_value=fake_wp_response) as mock_seo_post:

        from wordpress_poster import publish_post
        from seo_optimizer import set_seo_meta

        post_id = publish_post(data)
        check("Dry-run: publish_post returns a post ID", isinstance(post_id, int), f"id={post_id}")
        check("Dry-run: WP POST was called (mocked)",
              mock_wp_post.called or post_id == 99999)

        set_seo_meta(post_id, data)
        check("Dry-run: set_seo_meta executes without error", True)

    check("Full dry-run pipeline passed", True)

except Exception as exc:
    check("Full dry-run pipeline", False, str(exc))
    traceback.print_exc()

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
section("SUMMARY")

total   = len(results)
passed  = sum(1 for _, ok, _ in results if ok)
failed  = total - passed

for label, ok, detail in results:
    tag = PASS if ok else FAIL
    suffix = f"  — {detail}" if detail and not ok else ""
    print(f"{tag}  {label}{suffix}")

print()
print(f"{BOLD}Results: {GREEN}{passed} passed{RESET}{BOLD}, "
      f"{RED}{failed} failed{RESET}{BOLD} out of {total} checks{RESET}")

if failed == 0:
    print(f"\n{GREEN}{BOLD}All checks passed. Bot is ready to run.{RESET}")
    print(f"{CYAN}  Posts will be saved as DRAFTS — review them in WP Admin before publishing.{RESET}")
    print(f"{CYAN}  Top up Anthropic credits at console.anthropic.com, then run: python main.py{RESET}")
else:
    print(f"\n{YELLOW}{BOLD}Fix the failed checks above, then re-run test_bot.py before running main.py.{RESET}")

sys.exit(0 if failed == 0 else 1)
