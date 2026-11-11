"""Collect business profile details for a list of accounts into leads.csv.

Every PRO post item carries the account's profile: account type, category,
website, bio links, follower and post counts, and the email, phone, city and
address the profile shows publicly. One post per account is enough, so this
reads exactly one post per account and writes one CSV row per account.

Usage:
    export APIFY_TOKEN=your_token_here
    python business_leads_to_csv.py redbull dennikn heineken

Cost: one run per account (maxPosts is one total per run, filled account by
account, so a single run with maxPosts 1 would return only the first
account). Each account costs about $0.005 run start + $0.002 profile scan +
$0.0029 post = $0.0099.

Lawful basis: contact details here are only what each profile shows to any
visitor, but they can still be personal data (a sole trader's email, a
creator's phone). Before you contact anyone, make sure you have a lawful
basis for it under the law that applies to you and the recipient (for
example GDPR legitimate interest with a documented assessment, or consent
where the recipient's country requires it for marketing), do not use it for
private individuals, honour opt-outs, and delete what you no longer need.

Requires: pip install apify-client
"""

import csv
import sys

from scrape_posts_pro import scrape

FIELDS = [
    "username", "full_name", "is_verified", "owner_account_type",
    "owner_category", "follower_count", "owner_post_count", "owner_website",
    "owner_bio_links", "owner_public_email", "owner_public_phone",
    "owner_city", "owner_address",
]
LIST_FIELDS = {"owner_bio_links"}


def _defuse(value):
    """Neutralise spreadsheet formula injection.

    Profile fields are attacker-controlled: anyone can put `=HYPERLINK(...)`
    in a bio or display name. Excel and Sheets evaluate a cell starting with
    = + - @ as a formula on open, so prefix those with a quote and keep them
    as literal text.
    """
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def one_row_per_account(posts: list[dict]) -> list[dict]:
    """Keep the first post seen for each account (dedup on user_pk)."""
    seen: set = set()
    rows = []
    for post in posts:
        key = post.get("user_pk") or post.get("username")
        if key in seen:
            continue
        seen.add(key)
        rows.append(post)
    return rows


def to_csv(posts: list[dict], path: str = "leads.csv") -> int:
    rows = one_row_per_account(posts)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for post in rows:
            row = dict(post)
            for field in LIST_FIELDS:
                if isinstance(row.get(field), list):
                    row[field] = " ".join(row[field])
            writer.writerow({k: _defuse(v) for k, v in row.items()})
    return len(rows)


if __name__ == "__main__":
    usernames = sys.argv[1:] or ["redbull"]
    posts: list[dict] = []
    for username in usernames:
        # One failed run should not throw away the accounts already read
        # (and paid for): report it and move on to the next account.
        try:
            posts.extend(scrape([username], max_posts=1))
        except RuntimeError as exc:
            print(f"@{username}: {exc}", file=sys.stderr)
    count = to_csv(posts)
    print(f"wrote {count} accounts to leads.csv")
