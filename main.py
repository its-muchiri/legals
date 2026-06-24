"""
Legals Bot — main entry point.

Commands
--------
  python main.py --run                            Generate content and post all pending keywords as drafts
  python main.py --run -k "keyword"               Process a single keyword
  python main.py --run --site american-counsel    Post to american-counsel.com instead
  python main.py --run --site greenafrica         Post to greenafrica.co.ke instead
  python main.py --set-focus-keyword              Set Rank Math focus keyword on every processed post
  python main.py --set-categories-tags            Re-apply categories and tags to every processed post
  python main.py --publish                        Publish all draft posts
  python main.py --publish --limit 1              Publish one post (test)
  python main.py --publish --delay 10             Publish with 10-second gaps
  python main.py --full-pipeline                  Run all four steps in sequence
"""

import os
import sys

# Must set SITE before importing config — config reads env vars at module load time.
_site_idx = next((i for i, a in enumerate(sys.argv) if a == "--site"), None)
if _site_idx is not None and _site_idx + 1 < len(sys.argv):
    os.environ["SITE"] = sys.argv[_site_idx + 1]

import argparse
import time
from datetime import datetime
from typing import Optional

from config import DELAY_BETWEEN_POSTS, SITE
from claude_generator import generate_content
from excel_reader import (
    get_pending_keywords,
    load_processed_log,
    load_tags,
    mark_failed,
    mark_processed,
    save_post_record,
    save_processed_log,
)
from logger import get_logger
from seo_optimizer import set_rankmath_focus_keyword, set_seo_meta
from wordpress_poster import (
    _with_retry,
    get_post_info,
    patch_post_status,
    patch_post_terms,
    publish_post,
    resolve_categories,
    resolve_tags,
)

log = get_logger()

SEPARATOR = "=" * 60


def _phase(title: str) -> None:
    log.info(SEPARATOR)
    log.info(title)
    log.info(SEPARATOR)


def _log_active_site() -> None:
    from config import WP_URL
    log.info(f"Active site: {SITE} ({WP_URL})")


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND 1 — --run
# ─────────────────────────────────────────────────────────────────────────────

def _process_one(keyword: str, index: int, total: int, log_data: dict,
                 skip_terms: bool = False) -> None:
    log.info(f"Processing keyword {index}/{total}: {keyword}")
    try:
        # 1. Generate content
        data = generate_content(keyword)

        # 2. Post to WordPress as draft
        result = publish_post(data, skip_terms=skip_terms)
        post_id      = result["post_id"]
        post_slug    = result["slug"]
        post_link    = result["link"]
        category_ids = result["category_ids"]
        tag_ids      = result["tag_ids"]

        # 3. SEO meta (immediate, non-fatal)
        set_seo_meta(post_id, data)

        # 4. Build rich log record
        record = {
            "post_id":         post_id,
            "slug":            post_slug,
            "status":          "draft",
            "focus_keyphrase": data.get("focus_keyphrase", ""),
            "seo_title":       data.get("seo_title", ""),
            "meta_description":data.get("meta_description", ""),
            "categories":      data.get("categories", []),
            "tags":            data.get("tags", []),
            "category_ids":    category_ids,
            "tag_ids":         tag_ids,
            "published_url":   None,
            "date_processed":  datetime.now().isoformat(),
            "date_published":  None,
        }
        save_post_record(keyword, record, log_data)
        mark_processed(keyword, post_id, log_data)

        # 5. Token usage
        usage = data.get("_token_usage")
        if usage:
            log_data.setdefault("token_usage", {})[keyword] = usage
            save_processed_log(log_data)

        log.info(f"Draft saved. Moving to next keyword in {DELAY_BETWEEN_POSTS}s...")

    except Exception as exc:
        log.error(f"Failed to process '{keyword}': {exc}", exc_info=True)
        mark_failed(keyword, log_data)


def cmd_run(keyword: Optional[str] = None, limit: Optional[int] = None,
            skip_terms: bool = False) -> None:
    label = "Generating drafts (no categories/tags)" if skip_terms else "Generating content and posting drafts"
    _phase(label)
    _log_active_site()

    if keyword:
        log_data = load_processed_log()
        _process_one(keyword.strip(), 1, 1, log_data, skip_terms=skip_terms)
        return

    pending, log_data = get_pending_keywords()
    if not pending:
        log.info("No pending keywords. All done!")
        return

    if limit:
        pending = pending[:limit]

    total = len(pending)
    for idx, kw in enumerate(pending, start=1):
        _process_one(kw, idx, total, log_data, skip_terms=skip_terms)
        if idx < total:
            time.sleep(DELAY_BETWEEN_POSTS)

    processed_count = len(log_data["processed"])
    failed_count    = len(log_data["failed"])
    log.info(SEPARATOR)
    log.info(f"Run complete. Processed={processed_count}, Failed={failed_count}")
    log.info(SEPARATOR)


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND 2 — --set-focus-keyword
# ─────────────────────────────────────────────────────────────────────────────

def cmd_set_focus_keyword(limit: Optional[int] = None, delay: int = 5) -> None:
    """
    Set Rank Math focus keyword, SEO title, and meta description on all posts.

    IMPORTANT: Rank Math must have REST API meta enabled.
    WordPress Admin -> Rank Math -> General Settings -> REST API
    -> Enable "Add meta values in REST API responses" -> Save.
    If meta fields still don't save, install the plugin "REST API Meta Support".
    """
    _phase("Setting Rank Math focus keywords")

    log_data = load_processed_log()
    posts    = log_data.get("posts", {})

    if not posts:
        log.warning(
            "No posts found in processed_keywords.json. "
            "Run --run first to generate and post content."
        )
        return

    items = list(posts.items())
    if limit:
        items = items[:limit]

    success = failed = 0

    for keyword, record in items:
        post_id         = record.get("post_id")
        focus_keyphrase = record.get("focus_keyphrase", keyword)
        seo_title       = record.get("seo_title", "")
        meta_description= record.get("meta_description", "")

        if not post_id:
            log.warning(f"No post_id for '{keyword}' — skipping.")
            failed += 1
            continue

        ok = set_rankmath_focus_keyword(
            post_id, focus_keyphrase, seo_title, meta_description
        )
        if ok:
            success += 1
        else:
            failed += 1

        time.sleep(delay)

    log.info(SEPARATOR)
    log.info(f"Focus keywords set: {success} posts. Failed: {failed} posts.")
    log.info(SEPARATOR)


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND 3 — --set-categories-tags
# ─────────────────────────────────────────────────────────────────────────────

def cmd_set_categories_tags(limit: Optional[int] = None, delay: int = 5) -> None:
    """
    Re-apply categories and tags to every processed post.
    Safe to run multiple times — will not create duplicate terms.
    """
    _phase("Setting categories and tags")

    log_data  = load_processed_log()
    posts     = log_data.get("posts", {})
    file_tags = load_tags()

    if not posts:
        log.warning("No posts found in processed_keywords.json. Run --run first.")
        return

    items = list(posts.items())
    if limit:
        items = items[:limit]

    success = failed = 0

    for keyword, record in items:
        post_id    = record.get("post_id")
        categories = record.get("categories", [])
        tag_names  = file_tags if file_tags else record.get("tags", [])

        if not post_id:
            log.warning(f"No post_id for '{keyword}' — skipping.")
            failed += 1
            continue

        log.info(f"Updating terms for post {post_id} ({keyword[:50]}...)")
        try:
            cat_ids = _with_retry(resolve_categories, categories)
            tag_ids = _with_retry(resolve_tags, tag_names)
            _with_retry(patch_post_terms, post_id, cat_ids, tag_ids)

            # Update stored IDs
            record["category_ids"] = cat_ids
            record["tag_ids"]      = tag_ids
            save_post_record(keyword, record, log_data)

            success += 1
        except Exception as exc:
            log.error(f"  Failed for post {post_id}: {exc}")
            failed += 1

        time.sleep(delay)

    log.info(SEPARATOR)
    log.info(f"Categories/tags updated: {success} posts. Failed: {failed} posts.")
    log.info(SEPARATOR)


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND 4 — --publish
# ─────────────────────────────────────────────────────────────────────────────

def cmd_publish(limit: Optional[int] = None, delay: int = 5) -> None:
    """Publish all draft posts. Skips posts already published."""
    _phase("Publishing draft posts")

    log_data = load_processed_log()
    posts    = log_data.get("posts", {})

    if not posts:
        log.warning("No posts found in processed_keywords.json. Run --run first.")
        return

    # Collect all draft entries
    drafts = [
        (kw, rec) for kw, rec in posts.items()
        if rec.get("status") not in ("published", "publish")
    ]

    if not drafts:
        log.info("No draft posts to publish. All done!")
        return

    if limit:
        drafts = drafts[:limit]

    success = skipped = failed = 0

    for keyword, record in drafts:
        post_id = record.get("post_id")
        if not post_id:
            log.warning(f"No post_id for '{keyword}' — skipping.")
            skipped += 1
            continue

        # Check live status first
        try:
            info = _with_retry(get_post_info, post_id)
            if info["status"] in ("publish", "published"):
                log.info(f"Already published: post ID {post_id}")
                record["status"]        = "published"
                record["published_url"] = info["link"]
                save_post_record(keyword, record, log_data)
                skipped += 1
                continue
        except Exception as exc:
            log.warning(f"Could not fetch status for post {post_id}: {exc}. Attempting publish anyway.")

        log.info(f"Publishing post {post_id} ({keyword[:50]}...)")
        try:
            link = _with_retry(patch_post_status, post_id, "publish")
            record["status"]        = "published"
            record["published_url"] = link
            record["date_published"] = datetime.now().isoformat()
            save_post_record(keyword, record, log_data)

            log.info(f"  Published: {link}")
            success += 1
        except Exception as exc:
            log.error(f"  Failed to publish post {post_id}: {exc}")
            failed += 1

        time.sleep(delay)

    log.info(SEPARATOR)
    log.info(
        f"Published: {success} posts. "
        f"Skipped (already published): {skipped}. "
        f"Failed: {failed}."
    )
    log.info(SEPARATOR)


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND 5 — --full-pipeline
# ─────────────────────────────────────────────────────────────────────────────

def cmd_full_pipeline(limit: Optional[int] = None, delay: int = 5) -> None:
    """Run all four steps in sequence: run -> focus-keyword -> categories-tags -> publish."""

    _phase("FULL PIPELINE STARTING")

    _phase("PHASE 1: Generating and posting drafts")
    cmd_run(limit=limit)

    _phase("PHASE 2: Setting Rank Math focus keywords")
    cmd_set_focus_keyword(limit=limit, delay=delay)

    _phase("PHASE 3: Setting categories and tags")
    cmd_set_categories_tags(limit=limit, delay=delay)

    _phase("PHASE 4: Publishing all drafts")
    cmd_publish(limit=limit, delay=delay)

    _phase("FULL PIPELINE COMPLETE")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Legals Bot — WordPress content automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --run                                   Process all pending keywords -> legal-counsel.net
  python main.py --run --site american-counsel           Process all pending keywords -> american-counsel.com
  python main.py --run --site greenafrica                Process all pending keywords -> greenafrica.co.ke
  python main.py --run --site elisamotors                Process all pending keywords -> elisamotors.co.ke
  python main.py --run -k "keyword here"                 Process one specific keyword
  python main.py --draft-only                            Generate drafts only, skip categories + tags
  python main.py --draft-only --site greenafrica         Draft-only for greenafrica.co.ke
  python main.py --set-focus-keyword                     Set Rank Math meta on all posts
  python main.py --set-categories-tags                   Re-apply categories + tags
  python main.py --publish                               Publish all drafts
  python main.py --publish --limit 1                     Publish one draft (test)
  python main.py --publish --delay 10                    Publish with 10s gap between posts
  python main.py --full-pipeline                         Run all steps in sequence
        """,
    )

    parser.add_argument("--run",                  action="store_true", help="Generate content and post as drafts (with categories + tags)")
    parser.add_argument("--draft-only",           action="store_true", help="Generate drafts only — no categories or tags (fastest)")
    parser.add_argument("--set-focus-keyword",    action="store_true", help="Set Rank Math focus keyword on all posts")
    parser.add_argument("--set-categories-tags",  action="store_true", help="Set categories and tags on all posts")
    parser.add_argument("--publish",              action="store_true", help="Publish all draft posts")
    parser.add_argument("--full-pipeline",        action="store_true", help="Run all steps in sequence")
    parser.add_argument("-k", "--keyword",        type=str, default=None, help="Single keyword (used with --run)")
    parser.add_argument("--limit",                type=int, default=None, help="Limit number of posts to process")
    parser.add_argument("--delay",                type=int, default=5,    help="Delay in seconds between posts (default: 5)")
    parser.add_argument("--site",                 type=str, default=None, choices=["legal-counsel", "american-counsel", "greenafrica", "elisamotors"],
                        help="Target site (default: legal-counsel). NOTE: this flag is parsed before imports.")

    args = parser.parse_args()

    if args.draft_only:
        cmd_run(keyword=args.keyword, limit=args.limit, skip_terms=True)

    elif args.run or args.keyword:
        cmd_run(keyword=args.keyword, limit=args.limit)

    elif args.set_focus_keyword:
        cmd_set_focus_keyword(limit=args.limit, delay=args.delay)

    elif args.set_categories_tags:
        cmd_set_categories_tags(limit=args.limit, delay=args.delay)

    elif args.publish:
        cmd_publish(limit=args.limit, delay=args.delay)

    elif args.full_pipeline:
        cmd_full_pipeline(limit=args.limit, delay=args.delay)

    else:
        parser.print_help()
