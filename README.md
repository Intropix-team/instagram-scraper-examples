# Instagram Scraper API Examples in Python and Node

Instagram scraper API examples in Python and Node for three Apify actors that turn public Instagram stories, posts and reels into structured JSON. No login, no cookies, no OAuth and no Instagram account of your own, including age-restricted (18+) brand accounts that anonymous viewers cannot see:

- [Instagram Stories Scraper](https://apify.com/intropix/instagram-stories-scraper): active stories (they expire after 24 hours).
- [Instagram Posts & Reels Scraper](https://apify.com/intropix/instagram-posts-reels-scraper): posts and reels with likes, comments, real reel view counts and date-range filtering.
- [PRO Instagram Posts & Reels Scraper](https://apify.com/intropix/instagram-posts-reels-scraper-pro): everything in the standard scraper plus shares, reposts, music, location, tagged accounts, sponsor brands and the account's business profile details.

Every example needs an Apify API token: free account at [apify.com](https://apify.com), then Console > Settings > API & Integrations. On the Apify free plan you can test with up to 10 results per run and 40 results per day, shared across our Instagram actors, which is enough to run all of these.

## Examples

| File | What it does |
| --- | --- |
| [`python/scrape_stories.py`](python/scrape_stories.py) | Scrape active stories for a list of usernames, print results (apify-client) |
| [`python/stories_to_csv.py`](python/stories_to_csv.py) | Scrape stories and flatten to `stories.csv`, ready for Sheets or Excel |
| [`node/scrape-stories.mjs`](node/scrape-stories.mjs) | Zero-dependency Node 18+ stories version using the REST API |
| [`python/scrape_posts.py`](python/scrape_posts.py) | Scrape posts and reels (optional `SINCE_DATE`/`UNTIL_DATE`), print results |
| [`python/posts_to_csv.py`](python/posts_to_csv.py) | Scrape posts and flatten to `posts.csv`, carousel slides collapsed to one row |
| [`node/scrape-posts.mjs`](node/scrape-posts.mjs) | Zero-dependency Node 18+ posts version using the REST API |
| [`python/scrape_posts_pro.py`](python/scrape_posts_pro.py) | PRO: scrape posts and reels with shares, music, location and sponsors, print results |
| [`python/brand_deals_to_csv.py`](python/brand_deals_to_csv.py) | PRO: keep only sponsored / paid partnership posts, write `brand_deals.csv` |
| [`python/business_leads_to_csv.py`](python/business_leads_to_csv.py) | PRO: one row per account with category, website and public contact details, write `leads.csv` |
| [`node/scrape-posts-pro.mjs`](node/scrape-posts-pro.mjs) | PRO: zero-dependency Node 18+ version using the REST API |

## Quick start

```bash
export APIFY_TOKEN=your_token_here
pip install -r python/requirements.txt

# Stories
python python/scrape_stories.py natgeo nasa
node node/scrape-stories.mjs natgeo

# Posts and reels
python python/scrape_posts.py natgeo
SINCE_DATE=2026-07-01 python python/scrape_posts.py natgeo   # date-bounded
node node/scrape-posts.mjs natgeo

# PRO posts and reels
python python/scrape_posts_pro.py redbull
SINCE_DATE=2026-10-01 MAX_POSTS=30 python python/brand_deals_to_csv.py natgeo redbull nike
python python/business_leads_to_csv.py redbull heineken
node node/scrape-posts-pro.mjs redbull
```

## Output schemas

**Stories**, one dataset item per story, fixed 22 fields:

`username`, `user_pk`, `full_name`, `is_verified`, `is_private`, `story_pk`, `taken_at`, `expiring_at`, `media_type`, `media_url`, `video_duration`, `is_paid_partnership`, `attribution_url`, `width`, `height`, `caption`, `link_urls`, `hashtags`, `mentions`, `music_title`, `music_artist`, `coauthors`

**Posts and reels**, one dataset item per post, fixed 24 fields (a carousel is one item with every slide nested under `media`):

`username`, `user_pk`, `full_name`, `is_verified`, `is_private`, `follower_count`, `following_count`, `profile_pic_url`, `biography`, `post_pk`, `shortcode`, `permalink`, `post_type`, `taken_at`, `caption`, `like_count`, `comment_count`, `view_count`, `is_paid_partnership`, `is_off_grid`, `coauthors`, `hashtags`, `mentions`, `media[]`

**PRO posts and reels**, one dataset item per post, fixed 54 fields: the 24 above, in the same shape, plus:

`share_count`, `repost_count`, `fb_play_count`, `fb_like_count`, `engagement_rate`, `audio_title`, `audio_artist`, `audio_id`, `is_original_audio`, `sponsor_usernames`, `tagged_usernames`, `partners`, `is_pinned`, `caption_edited`, `has_audio`, `counts_hidden`, `location_name`, `location_id`, `location_city`, `location_lat`, `location_lng`, `owner_category`, `owner_account_type`, `owner_website`, `owner_bio_links`, `owner_post_count`, `owner_public_email`, `owner_public_phone`, `owner_city`, `owner_address`

Notes:

- `media_url` (stories) and each slide's `media_url` (posts) are direct CDN links to the full-resolution file; links expire, so download in the same job if you want the file.
- Stories die 24h after posting: `expiring_at` is your download deadline.
- `story_pk` / `post_pk` are stable numeric IDs; use them for dedup.
- Posts `like_count` and `comment_count` are null where Instagram hides them. `view_count` is a play count on reels and videos; photos and carousels have none, so it is null there rather than a misleading zero.
- `profile_pic_url` is the account's picture at the best resolution Instagram returns, and expires like the media links. `biography` is the profile bio as written.
- `is_off_grid` marks a reel that was not on the profile grid the run read. Opt in with `includeOffGridReels`; the field is present either way. Instagram trial reels are a separate case and are not returned: Instagram shows them only to the reel's author, so they are in no account listing a scraper can read.
- `maxPosts` is one total for the whole run, filled account by account in input order. To get N posts from every account, run once per account (as `brand_deals_to_csv.py` and `business_leads_to_csv.py` do) or use date bounds.
- Failed lookups (typos, deleted accounts) are never charged.

### PRO field highlights

- **Brand deals:** `is_paid_partnership`, `sponsor_usernames` (the brand on the paid partnership label), `coauthors`, `tagged_usernames`, and with `enrichPartners` on, `partners` (follower count, verified badge, category and account type of every co-author and sponsor).
- **Engagement:** `share_count`, `repost_count`, `engagement_rate` ((likes + comments) / followers, as a fraction).
- **Music:** `audio_title`, `audio_artist`, `audio_id`, `is_original_audio`.
- **Location:** `location_name`, `location_city`, `location_lat`, `location_lng`, `location_id`.
- **Business profile:** `owner_account_type`, `owner_category`, `owner_website`, `owner_bio_links`, `owner_post_count`, and `owner_public_email`, `owner_public_phone`, `owner_city`, `owner_address` only where the profile shows them publicly.

If captions, likes, comments, views and dates are all you need, the standard [Instagram Posts & Reels Scraper](https://apify.com/intropix/instagram-posts-reels-scraper) returns those at $1.90 per 1,000 posts. Its 24 fields are the first 24 of the PRO schema with the same names, and both take the same input, so code that reads only those fields works with either actor.

## Pricing

Pay-per-event, no subscription:

- **Stories:** $0.005 per run start, $0.002 per profile scanned, $0.0025 per story delivered. From $2.50 per 1,000 stories.
- **Posts and reels:** $0.005 per run start, $0.002 per profile scanned, $0.0019 per post delivered (a carousel is one post). From $1.90 per 1,000 posts.
- **PRO posts and reels:** $0.005 per run start, $0.002 per profile scanned, $0.0039 per post delivered (a carousel is one post). From $3.90 per 1,000 posts. Optional partner enrichment is $0.005 per enriched profile.

Full details on each actor page ([stories](https://apify.com/intropix/instagram-stories-scraper), [posts](https://apify.com/intropix/instagram-posts-reels-scraper), [PRO posts](https://apify.com/intropix/instagram-posts-reels-scraper-pro)).

## No-code and other integrations

The same actors run from the Apify API, n8n (the verified Apify node), Make, Zapier, and AI agents through Apify's MCP server. Actor ids for API use: `intropix~instagram-stories-scraper`, `intropix~instagram-posts-reels-scraper`, `intropix~instagram-posts-reels-scraper-pro`.

## Use responsibly

These actors read publicly visible content of business, creator and brand accounts; private accounts are out of scope. You are responsible for using the data lawfully, including any contact details. This is an independent project, not affiliated with, endorsed by, or connected to Instagram or Meta Platforms, Inc.

## Support

Issues tab on the actor page ([stories](https://apify.com/intropix/instagram-stories-scraper/issues), [posts](https://apify.com/intropix/instagram-posts-reels-scraper/issues), [PRO posts](https://apify.com/intropix/instagram-posts-reels-scraper-pro/issues)), or team.intropix@gmail.com.
