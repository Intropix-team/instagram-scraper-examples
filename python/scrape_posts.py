"""Scrape Instagram posts and reels for one or more usernames.

Usage:
    export APIFY_TOKEN=your_token_here
    python scrape_posts.py natgeo nasa

Optional date bounds (YYYY-MM-DD, UTC) via env vars:
    SINCE_DATE=2026-07-01 UNTIL_DATE=2026-07-31 python scrape_posts.py natgeo

Requires: pip install apify-client
"""

import json
import os
import sys

from apify_client import ApifyClient

ACTOR = "intropix/instagram-posts-reels-scraper"


def scrape(usernames: list[str], max_posts: int = 10) -> list[dict]:
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        sys.exit("APIFY_TOKEN is not set. Export it before running.")
    client = ApifyClient(token)

    run_input: dict = {"usernames": usernames, "maxPosts": max_posts}
    # sinceDate/untilDate bound the fetch server-side, so a scheduled daily run
    # with yesterday's date collects only the new posts instead of the feed.
    if os.environ.get("SINCE_DATE"):
        run_input["sinceDate"] = os.environ["SINCE_DATE"]
    if os.environ.get("UNTIL_DATE"):
        run_input["untilDate"] = os.environ["UNTIL_DATE"]

    run = client.actor(ACTOR).call(run_input=run_input)
    if run["status"] != "SUCCEEDED":
        raise RuntimeError(f"run finished with status {run['status']}")

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
    posts = scrape(usernames)
    if not sys.stdout.isatty():
        # piped: emit clean JSON (python scrape_posts.py natgeo > posts.json)
        print(json.dumps(posts, indent=2))
    else:
        print(f"{len(posts)} posts for {', '.join(usernames)}\n")
        for p in posts:
            # .get() throughout: the output schema is stable but evolves, and a
            # missing field should not crash the example. A carousel is one item
            # with every slide nested under "media".
            slides = p.get("media") or []
            print(f"@{p.get('username')} [{p.get('post_type')}] "
                  f"{p.get('taken_at')} likes={p.get('like_count')} "
                  f"comments={p.get('comment_count')} slides={len(slides)}")
            print(f"  {p.get('permalink')}")
            if p.get("is_paid_partnership"):
                print("  paid partnership")
            if p.get("coauthors"):
                print(f"  coauthors: {', '.join(p['coauthors'])}")
