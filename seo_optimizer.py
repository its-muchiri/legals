from __future__ import annotations

import time
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from config import SEO_PLUGIN, WP_APP_PASSWORD, WP_URL, WP_USERNAME
from logger import get_logger

log = get_logger()

# IMPORTANT: For Rank Math meta fields to save via the REST API:
# 1. Go to WordPress Admin -> Rank Math -> General Settings
# 2. Click the "REST API" tab
# 3. Enable "Add meta values in REST API responses"
# 4. Save settings
#
# If meta fields still don't save after that, install the free plugin
# "REST API Meta Support" from the WordPress plugin repository.


def _auth() -> HTTPBasicAuth:
    return HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)


def _api(path: str) -> str:
    return f"{WP_URL.rstrip('/')}/wp-json/wp/v2/{path.lstrip('/')}"


def _build_meta(data: dict[str, Any]) -> dict[str, str]:
    seo_title  = data.get("seo_title", "")
    meta_desc  = data.get("meta_description", "")
    focus_kw   = data.get("focus_keyphrase", "")

    if SEO_PLUGIN == "rankmath":
        return {
            "rank_math_title":         seo_title,
            "rank_math_description":   meta_desc,
            "rank_math_focus_keyword": focus_kw,
        }

    # Default: Yoast SEO
    return {
        "_yoast_wpseo_title":    seo_title,
        "_yoast_wpseo_metadesc": meta_desc,
        "_yoast_wpseo_focuskw":  focus_kw,
    }


def set_seo_meta(post_id: int, data: dict[str, Any]) -> None:
    """Called immediately after post creation (existing flow). Non-fatal."""
    plugin_label = "Rank Math" if SEO_PLUGIN == "rankmath" else "Yoast"
    log.info(f"Setting {plugin_label} SEO meta fields...")

    meta = _build_meta(data)
    resp = requests.post(
        _api(f"posts/{post_id}"),
        json={"meta": meta},
        auth=_auth(),
        timeout=30,
    )

    if not resp.ok:
        log.warning(
            f"SEO meta update returned HTTP {resp.status_code}: {resp.text[:300]}\n"
            "  -> Check Rank Math > General Settings > REST API > enable meta fields."
        )
        return

    log.info(f"SEO optimized (post_id={post_id}).")


def set_rankmath_focus_keyword(
    post_id: int,
    focus_keyphrase: str,
    seo_title: str,
    meta_description: str,
    *,
    retries: int = 1,
    retry_wait: int = 3,
) -> bool:
    """
    Standalone Rank Math meta updater used by --set-focus-keyword.
    Returns True on success, False on failure.

    IMPORTANT: Rank Math must have REST API meta enabled.
    WordPress Admin -> Rank Math -> General Settings -> REST API
    -> Enable "Add meta values in REST API responses" -> Save.
    """
    meta = {
        "rank_math_focus_keyword": focus_keyphrase,
        "rank_math_title":         seo_title,
        "rank_math_description":   meta_description,
    }

    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                _api(f"posts/{post_id}"),
                json={"meta": meta},
                auth=_auth(),
                timeout=30,
            )
            if not resp.ok:
                raise RuntimeError(
                    f"HTTP {resp.status_code}: {resp.text[:300]}\n"
                    "  -> Check Rank Math REST API settings (see comment at top of seo_optimizer.py)."
                )
            log.info(f"  [OK] Focus keyword set for post {post_id}: \"{focus_keyphrase}\"")
            return True

        except Exception as exc:
            if attempt < retries:
                log.warning(f"  Attempt {attempt + 1} failed for post {post_id}: {exc}. Retrying in {retry_wait}s...")
                time.sleep(retry_wait)
            else:
                log.error(f"  [FAIL] Post {post_id}: {exc}")
                return False

    return False
