from __future__ import annotations

import time
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from config import WP_APP_PASSWORD, WP_POST_STATUS, WP_URL, WP_USERNAME
from excel_reader import load_tags
from logger import get_logger

log = get_logger()


# ── Shared helpers ────────────────────────────────────────────────────────────

def _auth() -> HTTPBasicAuth:
    return HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)


def _api(path: str) -> str:
    return f"{WP_URL.rstrip('/')}/wp-json/wp/v2/{path.lstrip('/')}"


def _raise_for_status(resp: requests.Response, context: str) -> None:
    if not resp.ok:
        raise RuntimeError(
            f"{context} — HTTP {resp.status_code}: {resp.text[:400]}"
        )


def _with_retry(fn, *args, retries: int = 1, wait: int = 3, **kwargs):
    """Call fn(*args, **kwargs), retrying up to `retries` times on failure."""
    for attempt in range(retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            if attempt < retries:
                log.warning(f"Attempt {attempt + 1} failed: {exc}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


# ── Term resolution (categories / tags) ──────────────────────────────────────

def _get_or_create_term(endpoint: str, name: str) -> int:
    """Return the WP term ID for *name*, creating it if absent. Idempotent."""
    slug = name.lower().replace(" ", "-")

    resp = requests.get(
        _api(endpoint),
        params={"slug": slug, "per_page": 1},
        auth=_auth(),
        timeout=30,
    )
    _raise_for_status(resp, f"GET {endpoint} '{name}'")
    results = resp.json()

    if results:
        term_id: int = results[0]["id"]
        log.debug(f"  Found existing {endpoint.rstrip('s')}: '{name}' (id={term_id})")
        return term_id

    log.info(f"  Creating {endpoint.rstrip('s')}: {name}")
    resp = requests.post(
        _api(endpoint),
        json={"name": name, "slug": slug},
        auth=_auth(),
        timeout=30,
    )
    _raise_for_status(resp, f"POST {endpoint} '{name}'")
    term_id = resp.json()["id"]
    log.debug(f"  Created {endpoint.rstrip('s')}: '{name}' (id={term_id})")
    return term_id


def resolve_categories(names: list[str]) -> list[int]:
    log.info(f"Resolving {len(names)} categories...")
    return [_get_or_create_term("categories", n) for n in names]


def resolve_tags(names: list[str]) -> list[int]:
    log.info(f"Resolving {len(names)} tags...")
    return [_get_or_create_term("tags", n) for n in names]


# ── Duplicate-slug check ──────────────────────────────────────────────────────

def slug_exists(slug: str) -> int | None:
    """Return post ID if a post with this slug already exists, else None.

    Tries status=any first; falls back to published-only if the user lacks
    permission to query all statuses (common for non-admin app passwords).
    """
    param_sets = [
        {"slug": slug, "per_page": 1, "status": "any"},
        {"slug": slug, "per_page": 1},  # published only — fallback
    ]
    for params in param_sets:
        resp = requests.get(
            _api("posts"),
            params=params,
            auth=_auth(),
            timeout=30,
        )
        if resp.status_code == 400 and "rest_forbidden_status" in resp.text:
            log.warning(
                f"Cannot query status=any for slug check (user lacks permission). "
                f"Falling back to published-only check."
            )
            continue
        _raise_for_status(resp, f"GET posts slug='{slug}'")
        results = resp.json()
        if results:
            existing_id: int = results[0]["id"]
            log.warning(f"Post with slug '{slug}' already exists (id={existing_id}). Skipping.")
            return existing_id
        return None
    return None


# ── Post info ─────────────────────────────────────────────────────────────────

def get_post_info(post_id: int) -> dict:
    """Fetch basic info for a post: status, link, slug."""
    resp = requests.get(
        _api(f"posts/{post_id}"),
        params={"context": "edit"},
        auth=_auth(),
        timeout=30,
    )
    _raise_for_status(resp, f"GET posts/{post_id}")
    p = resp.json()
    return {
        "status": p.get("status", ""),
        "link":   p.get("link", ""),
        "slug":   p.get("slug", ""),
    }


# ── Create draft ──────────────────────────────────────────────────────────────

def publish_post(data: dict[str, Any], skip_terms: bool = False) -> dict[str, Any]:
    """Create the WordPress post and return a result dict.

    Args:
        data:        Validated content dict from claude_generator.
        skip_terms:  If True, post is created without categories or tags.
                     Use --draft-only; run --set-categories-tags later to add them.

    Returns:
        {
          "post_id":      int,
          "slug":         str,
          "link":         str,
          "category_ids": list[int],
          "tag_ids":      list[int],
        }
    """
    slug = data["slug"]

    existing = slug_exists(slug)
    if existing:
        return {"post_id": existing, "slug": slug, "link": "", "category_ids": [], "tag_ids": []}

    if skip_terms:
        log.info("Skipping categories and tags (--draft-only mode).")
        category_ids = []
        tag_ids      = []
    else:
        category_ids = resolve_categories(data.get("categories", []))
        file_tags    = load_tags()
        tag_names    = file_tags if file_tags else data.get("tags", [])
        log.info(f"Using {len(tag_names)} tags from {'tags.txt' if file_tags else 'Claude response'}")
        tag_ids = resolve_tags(tag_names)

    log.info("Posting to WordPress as draft...")

    payload: dict[str, Any] = {
        "title":      data["title"],
        "content":    data["content"],
        "excerpt":    data.get("excerpt", ""),
        "slug":       slug,
        "status":     WP_POST_STATUS,
        "categories": category_ids,
        "tags":       tag_ids,
    }

    resp = requests.post(_api("posts"), json=payload, auth=_auth(), timeout=60)
    _raise_for_status(resp, "POST posts")

    post  = resp.json()
    post_id: int = post["id"]
    link:    str = post.get("link", "")
    log.info(f"Draft created: {link} (id={post_id})")

    return {
        "post_id":      post_id,
        "slug":         slug,
        "link":         link,
        "category_ids": category_ids,
        "tag_ids":      tag_ids,
    }


# ── Standalone patchers (used by new commands) ────────────────────────────────

def patch_post_terms(post_id: int, category_ids: list[int], tag_ids: list[int]) -> None:
    """PATCH a post's categories and tags. Safe to call repeatedly."""
    resp = requests.post(
        _api(f"posts/{post_id}"),
        json={"categories": category_ids, "tags": tag_ids},
        auth=_auth(),
        timeout=30,
    )
    _raise_for_status(resp, f"PATCH posts/{post_id} terms")
    log.info(f"  Terms updated for post {post_id}: "
             f"{len(category_ids)} categories, {len(tag_ids)} tags.")


def patch_post_status(post_id: int, status: str) -> str:
    """PATCH a post's status. Returns the post link on success."""
    resp = requests.post(
        _api(f"posts/{post_id}"),
        json={"status": status},
        auth=_auth(),
        timeout=30,
    )
    _raise_for_status(resp, f"PATCH posts/{post_id} status={status}")
    return resp.json().get("link", "")
