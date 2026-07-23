"""Scrape Instagram stories and write them to stories.csv.

The CSV opens directly in Google Sheets or Excel. List fields
(link_urls, mentions, hashtags, coauthors) are space-joined.

Usage:
    export APIFY_TOKEN=your_token_here
    python stories_to_csv.py natgeo nasa

Requires: pip install apify-client
"""

import csv
import sys

from scrape_stories import scrape

FIELDS = [
    "username", "full_name", "story_pk", "taken_at", "expiring_at",
    "media_type", "caption", "link_urls", "hashtags", "mentions",
    "coauthors", "music_title", "music_artist", "is_paid_partnership",
    "is_verified", "media_url",
]
LIST_FIELDS = {"link_urls", "hashtags", "mentions", "coauthors"}


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


def to_csv(stories: list[dict], path: str = "stories.csv") -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for story in stories:
            row = dict(story)
            for field in LIST_FIELDS:
                if isinstance(row.get(field), list):
                    row[field] = " ".join(row[field])
            writer.writerow({k: _defuse(v) for k, v in row.items()})


if __name__ == "__main__":
    usernames = sys.argv[1:] or ["natgeo"]
    stories = scrape(usernames)
    to_csv(stories)
    print(f"wrote {len(stories)} stories to stories.csv")
