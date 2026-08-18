# Instagram Scrapers: code examples

Runnable examples for two Apify actors that scrape Instagram to structured JSON with no login, cookies, or OAuth, including age-restricted (18+) brand accounts that anonymous viewers cannot see:

- [Instagram Stories Scraper](https://apify.com/intropix/instagram-stories-scraper): active stories (expire after 24h).
- [Instagram Posts & Reels Scraper](https://apify.com/intropix/instagram-posts-reels-scraper): posts and reels with engagement counts and date-range filtering.

Every example needs an Apify API token: free account at [apify.com](https://apify.com), then Console > Settings > API & Integrations. Each actor's free trial (10 results per run, about 20 per day, shared across both) is enough to run all of these.

## Examples

| File | What it does |
| --- | --- |
| [`python/scrape_stories.py`](python/scrape_stories.py) | Scrape active stories for a list of usernames, print results (apify-client) |
| [`python/stories_to_csv.py`](python/stories_to_csv.py) | Scrape stories and flatten to `stories.csv`, ready for Sheets or Excel |
| [`node/scrape-stories.mjs`](node/scrape-stories.mjs) | Zero-dependency Node 18+ stories version using the REST run-sync endpoint |
| [`python/scrape_posts.py`](python/scrape_posts.py) | Scrape posts and reels (optional `SINCE_DATE`/`UNTIL_DATE`), print results |
| [`python/posts_to_csv.py`](python/posts_to_csv.py) | Scrape posts and flatten to `posts.csv`, carousel slides collapsed to one row |
| [`node/scrape-posts.mjs`](node/scrape-posts.mjs) | Zero-dependency Node 18+ posts version using the REST run-sync endpoint |

## Quick start

```bash
export APIFY_TOKEN=your_token_here

# Stories
pip install apify-client
python python/scrape_stories.py natgeo nasa
node node/scrape-stories.mjs natgeo

# Posts and reels
python python/scrape_posts.py natgeo
SINCE_DATE=2026-07-01 python python/scrape_posts.py natgeo   # date-bounded
node node/scrape-posts.mjs natgeo
```

## Output schemas

**Stories**, one dataset item per story, fixed 22 fields:

`username`, `user_pk`, `full_name`, `is_verified`, `is_private`, `story_pk`, `taken_at`, `expiring_at`, `media_type`, `media_url`, `video_duration`, `is_paid_partnership`, `attribution_url`, `width`, `height`, `caption`, `link_urls`, `hashtags`, `mentions`, `music_title`, `music_artist`, `coauthors`

**Posts and reels**, one dataset item per post, fixed 24 fields (a carousel is one item with every slide nested under `media`):

`username`, `user_pk`, `full_name`, `is_verified`, `is_private`, `follower_count`, `following_count`, `profile_pic_url`, `biography`, `post_pk`, `shortcode`, `permalink`, `post_type`, `taken_at`, `caption`, `like_count`, `comment_count`, `view_count`, `is_paid_partnership`, `is_off_grid`, `coauthors`, `hashtags`, `mentions`, `media[]`

Notes:

- `media_url` (stories) and each slide's `media_url` (posts) are direct CDN links to the full-resolution file; links expire, so download in the same job if you want the file.
- Stories die 24h after posting: `expiring_at` is your download deadline.
- `story_pk` / `post_pk` are stable numeric IDs; use them for dedup.
- Posts `like_count` and `comment_count` are null where Instagram hides them. `view_count` is a play count on reels and videos; photos and carousels have none, so it is null there rather than a misleading zero.
- `profile_pic_url` is the account's picture at the best resolution Instagram returns, and expires like the media links. `biography` is the profile bio as written.
- `is_off_grid` marks a reel that was not on the profile grid the run read, including trial reels. Opt in with `includeOffGridReels`; the field is present either way.
- Failed lookups (typos, deleted accounts) are never charged.

## Pricing

Pay-per-event, no subscription:

- **Stories:** $0.005 per run start, $0.002 per profile scanned, $0.0025 per story delivered. From $2.50 per 1,000 stories.
- **Posts and reels:** $0.005 per run start, $0.002 per profile scanned, $0.0019 per post delivered (a carousel is one post). From $1.90 per 1,000 posts.

Full details on each actor page ([stories](https://apify.com/intropix/instagram-stories-scraper), [posts](https://apify.com/intropix/instagram-posts-reels-scraper)).

## No-code pipelines

Prefer n8n? There are ready-made templates for story archiving to Google Drive, competitor tracking to Sheets with an AI daily brief, influencer placement verification to Notion, and 18+ brand story monitoring with Slack alerts. Search "Instagram stories" in the n8n template gallery.

## Support

Issues tab on the actor page ([stories](https://apify.com/intropix/instagram-stories-scraper/issues), [posts](https://apify.com/intropix/instagram-posts-reels-scraper/issues)), or team.intropix@gmail.com.
