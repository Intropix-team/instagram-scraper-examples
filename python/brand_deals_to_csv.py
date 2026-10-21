"""Find sponsored posts (paid partnerships) and write them to brand_deals.csv.

Runs the PRO scraper on a list of creator or brand accounts and keeps only
the posts that carry Instagram's paid partnership label or name a sponsor
brand. One CSV row per sponsored post, with the sponsor, co-authors, tagged
accounts and the post's metrics side by side.

Usage:
    export APIFY_TOKEN=your_token_here
    python brand_deals_to_csv.py natgeo redbull nike

Optional env vars:
    SINCE_DATE=2026-10-01   only posts on or after this date (UTC)
    MAX_POSTS=30            posts read PER ACCOUNT (default 30)

Each account gets its own run, because maxPosts is one total per run filled
account by account in input order. Every post read is billed, sponsored or
not: about $0.0039 per post, plus $0.002 per account and $0.005 per run.

Requires: pip install apify-client
"""

import csv
import os
import sys

from scrape_posts_pro import scrape

FIELDS = [
    "username", "permalink", "post_type", "taken_at", "sponsor_usernames",
    "coauthors", "tagged_usernames", "like_count", "comment_count",
    "view_count", "share_count", "engagement_rate", "caption",
]
LIST_FIELDS = {"sponsor_usernames", "coauthors", "tagged_usernames"}


def _defuse(value):
    """Neutralise spreadsheet formula injection.

    Captions, display names and mentions are attacker-controlled: anyone can
    put `=HYPERLINK(...)` in an Instagram caption. Excel and Sheets evaluate a
    cell starting with = + - @ as a formula on open, so prefix those with a
    quote and keep them as literal text.
    """
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def is_sponsored(post: dict) -> bool:
    """A post is a brand deal when it carries the paid partnership label or
    names a sponsor brand on it."""
    return bool(post.get("is_paid_partnership") or post.get("sponsor_usernames"))


def to_csv(posts: list[dict], path: str = "brand_deals.csv") -> int:
    deals = [p for p in posts if is_sponsored(p)]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for post in deals:
            row = dict(post)
            for field in LIST_FIELDS:
                if isinstance(row.get(field), list):
                    row[field] = " ".join(row[field])
            writer.writerow({k: _defuse(v) for k, v in row.items()})
    return len(deals)


if __name__ == "__main__":
    usernames = sys.argv[1:] or ["natgeo"]
    per_account = int(os.environ.get("MAX_POSTS", "30"))
    posts: list[dict] = []
    for username in usernames:
        # One failed run should not throw away the accounts already read
        # (and paid for): report it and move on to the next account.
        try:
            posts.extend(scrape([username], max_posts=per_account))
        except RuntimeError as exc:
            print(f"@{username}: {exc}", file=sys.stderr)
    count = to_csv(posts)
    print(f"read {len(posts)} posts, wrote {count} sponsored posts to brand_deals.csv")
