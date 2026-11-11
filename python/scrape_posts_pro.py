"""Scrape Instagram posts and reels with the PRO scraper (54 fields per post).

Same input as the standard posts scraper, plus shares, reposts, music,
location, tagged accounts, sponsor brands and the account's profile details
in every item.

Usage:
    export APIFY_TOKEN=your_token_here
    python scrape_posts_pro.py natgeo nasa

Optional env vars:
    SINCE_DATE=2026-10-01 UNTIL_DATE=2026-10-31   date bounds (YYYY-MM-DD, UTC)
    ENRICH_PARTNERS=1   add a profile summary of every co-author and sponsor
                        brand ($0.0035 per enriched profile, paid plans only)

Note: maxPosts is ONE total for the whole run, filled account by account in
input order, so with several usernames the first account can use it all.
Raise MAX_POSTS, or run once per account (see business_leads_to_csv.py).

Requires: pip install apify-client
"""

from __future__ import annotations

import json
import os
import sys

from apify_client import ApifyClient

ACTOR = "intropix/instagram-posts-reels-scraper-pro"


def scrape(
    usernames: list[str],
    max_posts: int = 10,
    enrich_partners: bool = False,
    since_date: str | None = None,
    until_date: str | None = None,
) -> list[dict]:
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        sys.exit("APIFY_TOKEN is not set. Export it before running.")
    client = ApifyClient(token)

    run_input: dict = {
        "usernames": usernames,
        "maxPosts": max_posts,
        "enrichPartners": enrich_partners,
    }
    since_date = since_date or os.environ.get("SINCE_DATE")
    until_date = until_date or os.environ.get("UNTIL_DATE")
    if since_date:
        run_input["sinceDate"] = since_date
    if until_date:
        run_input["untilDate"] = until_date

    run = client.actor(ACTOR).call(run_input=run_input)
    if run is None or run["status"] != "SUCCEEDED":
        raise RuntimeError(f"run finished with status {run and run['status']}")

    # An empty result has two very different causes: the accounts genuinely
    # have no matching posts, or the run was refused (free daily limit, for
    # example). The dataset looks identical either way, so read the run's
    # OUTPUT record, which says which of the two happened.
    output = client.key_value_store(run["defaultKeyValueStoreId"]).get_record("OUTPUT")
    if output and output["value"].get("outcome") == "denied":
        value = output["value"]
        print(
            f"run refused ({value.get('reason')}): {value.get('message')}",
            file=sys.stderr,
        )
        return []

    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


if __name__ == "__main__":
    usernames = sys.argv[1:] or ["natgeo"]
    posts = scrape(
        usernames,
        max_posts=int(os.environ.get("MAX_POSTS", "10")),
        enrich_partners=os.environ.get("ENRICH_PARTNERS") == "1",
    )
    if not sys.stdout.isatty():
        # piped: emit clean JSON (python scrape_posts_pro.py natgeo > posts.json)
        print(json.dumps(posts, indent=2, ensure_ascii=False))
    else:
        print(f"{len(posts)} posts for {', '.join(usernames)}\n")
        for p in posts:
            # .get() throughout: the output schema is stable but evolves, and a
            # missing field should not crash the example.
            print(f"@{p.get('username')} [{p.get('post_type')}] {p.get('taken_at')} "
                  f"likes={p.get('like_count')} comments={p.get('comment_count')} "
                  f"views={p.get('view_count')} shares={p.get('share_count')}")
            print(f"  {p.get('permalink')}")
            if p.get("audio_title"):
                print(f"  audio: {p.get('audio_title')} by {p.get('audio_artist')}")
            if p.get("location_name"):
                print(f"  location: {p.get('location_name')} "
                      f"({p.get('location_lat')}, {p.get('location_lng')})")
            if p.get("is_paid_partnership") or p.get("sponsor_usernames"):
                sponsors = ", ".join(p.get("sponsor_usernames") or []) or "unnamed"
                print(f"  paid partnership, sponsor: {sponsors}")
            if p.get("tagged_usernames"):
                print(f"  tagged: {', '.join(p['tagged_usernames'])}")
