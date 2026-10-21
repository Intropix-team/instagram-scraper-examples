// Scrape Instagram posts and reels with the PRO scraper, zero dependencies
// (Node 18+). 54 fields per post: everything in the standard scraper plus
// shares, reposts, music, location, tagged accounts, sponsor brands and the
// account's profile details.
//
// Usage:
//   export APIFY_TOKEN=your_token_here
//   node scrape-posts-pro.mjs natgeo nasa
//
// maxPosts is one total for the whole run, filled account by account in
// input order, so with several usernames the first account can use it all.
//
// Starts the actor, waits for it to finish, then reads two things: the
// dataset (the posts) and the run's OUTPUT record (why the run ended the
// way it did). An empty dataset alone is ambiguous, since "no matching
// posts" and "run refused" both produce zero items.

const ACTOR = "intropix~instagram-posts-reels-scraper-pro";
const API = "https://api.apify.com/v2";

async function apiFetch(path, token, options = {}) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      // Sent as a header, not a query string: URLs end up in shell history,
      // proxy logs and server access logs, and the token would leak with them.
      Authorization: `Bearer ${token}`,
      ...(options.headers ?? {}),
    },
  });
  if (!res.ok) {
    throw new Error(`Apify API ${res.status}: ${await res.text()}`);
  }
  return res.json();
}

async function scrapePostsPro(usernames, maxPosts = 10, enrichPartners = false) {
  const token = process.env.APIFY_TOKEN;
  if (!token) {
    throw new Error("APIFY_TOKEN is not set. Export it before running.");
  }

  let { data: run } = await apiFetch(
    `/acts/${ACTOR}/runs?waitForFinish=60`,
    token,
    {
      method: "POST",
      body: JSON.stringify({ usernames, maxPosts, enrichPartners }),
    }
  );
  // waitForFinish caps at 60s per call and returns an unfinished run when it
  // expires, so keep waiting until the status is terminal rather than
  // mistaking a transitional one (READY, RUNNING, TIMING-OUT, ABORTING) for
  // the final result.
  const TERMINAL = new Set(["SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"]);
  while (!TERMINAL.has(run.status)) {
    ({ data: run } = await apiFetch(
      `/actor-runs/${run.id}?waitForFinish=60`,
      token
    ));
  }
  if (run.status !== "SUCCEEDED") {
    throw new Error(`run finished with status ${run.status}`);
  }

  // Tolerate a missing OUTPUT (404) rather than failing the whole scrape.
  const output = await apiFetch(
    `/key-value-stores/${run.defaultKeyValueStoreId}/records/OUTPUT`,
    token
  ).catch(() => null);

  if (output?.outcome === "denied") {
    console.error(`run refused (${output.reason}): ${output.message}`);
    return [];
  }

  return apiFetch(`/datasets/${run.defaultDatasetId}/items`, token);
}

const usernames = process.argv.slice(2);
const posts = await scrapePostsPro(usernames.length ? usernames : ["natgeo"]);

console.log(`${posts.length} posts`);
for (const p of posts) {
  console.log(
    `@${p.username} [${p.post_type}] ${p.taken_at} ` +
      `likes=${p.like_count} views=${p.view_count} shares=${p.share_count}`
  );
  console.log(`  ${p.permalink}`);
  if (p.audio_title) console.log(`  audio: ${p.audio_title} by ${p.audio_artist}`);
  if (p.location_name) console.log(`  location: ${p.location_name}`);
  if (p.is_paid_partnership || p.sponsor_usernames?.length) {
    console.log(`  sponsor: ${(p.sponsor_usernames ?? []).join(", ") || "unnamed"}`);
  }
}
