"""Scrape Instagram posts and reels and write them to posts.csv.

The CSV opens directly in Google Sheets or Excel, one row per post. The nested
media slides are flattened: `media_urls` is a space-joined list of every
slide's URL and `slide_count` is how many there are. List fields (hashtags,
mentions, coauthors) are space-joined.

Usage:
    export APIFY_TOKEN=your_token_here
    python posts_to_csv.py natgeo nasa

Requires: pip install apify-client
"""

import csv
import sys

from scrape_posts import scrape

FIELDS = [
    "username", "full_name", "post_pk", "shortcode", "permalink", "post_type",
    "taken_at", "caption", "like_count", "comment_count", "view_count",
    "is_paid_partnership", "hashtags", "mentions", "coauthors",
    "slide_count", "media_urls",
]
LIST_FIELDS = {"hashtags", "mentions", "coauthors"}


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


def to_csv(posts: list[dict], path: str = "posts.csv") -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for post in posts:
            row = dict(post)
            media = row.get("media") or []
            row["slide_count"] = len(media)
            row["media_urls"] = " ".join(
                m.get("media_url", "") for m in media if isinstance(m, dict)
            )
            for field in LIST_FIELDS:
                if isinstance(row.get(field), list):
                    row[field] = " ".join(row[field])
            writer.writerow({k: _defuse(v) for k, v in row.items()})


if __name__ == "__main__":
    usernames = sys.argv[1:] or ["natgeo"]
    posts = scrape(usernames)
    to_csv(posts)
    print(f"wrote {len(posts)} posts to posts.csv")
