"""Scrape active Instagram stories for one or more usernames.

Usage:
    export APIFY_TOKEN=your_token_here
    python scrape_stories.py natgeo nasa

Requires: pip install apify-client
"""

import json
import os
import sys

from apify_client import ApifyClient

ACTOR = "intropix/instagram-stories-scraper"


def scrape(usernames: list[str], max_results: int = 10) -> list[dict]:
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        sys.exit("APIFY_TOKEN is not set. Export it before running.")
    client = ApifyClient(token)
    run = client.actor(ACTOR).call(
        run_input={"usernames": usernames, "maxResults": max_results}
    )
    if run["status"] != "SUCCEEDED":
        raise RuntimeError(f"run finished with status {run['status']}")

    # An empty result has two very different causes: the accounts genuinely
    # have no active stories, or the run was refused (free daily limit, for
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
    stories = scrape(usernames)
    if not sys.stdout.isatty():
        # piped: emit clean JSON (python scrape_stories.py natgeo > stories.json)
        print(json.dumps(stories, indent=2))
    else:
        print(f"{len(stories)} active stories for {', '.join(usernames)}\n")
        for s in stories:
            # .get() throughout: the output schema is stable but evolves, and a
            # missing field should not crash the example.
            print(f"@{s.get('username')} [{s.get('media_type')}] "
                  f"posted {s.get('taken_at')}, expires {s.get('expiring_at')}")
            if s.get("mentions"):
                print(f"  mentions: {', '.join(s['mentions'])}")
            if s.get("link_urls"):
                print(f"  links: {' '.join(s['link_urls'])}")
