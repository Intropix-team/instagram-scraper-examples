// Scrape active Instagram stories, zero dependencies (Node 18+).
//
// Usage:
//   export APIFY_TOKEN=your_token_here
//   node scrape-stories.mjs natgeo nasa
//
// Starts the actor, waits for it to finish, then reads two things: the
// dataset (the stories) and the run's OUTPUT record (why the run ended the
// way it did). An empty dataset alone is ambiguous, since "no active
// stories" and "run refused" both produce zero items.

const ACTOR = "intropix~instagram-stories-scraper";
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

async function scrapeStories(usernames, maxResults = 10) {
  const token = process.env.APIFY_TOKEN;
  if (!token) {
    throw new Error("APIFY_TOKEN is not set. Export it before running.");
  }

  let { data: run } = await apiFetch(
    `/acts/${ACTOR}/runs?waitForFinish=60`,
    token,
    { method: "POST", body: JSON.stringify({ usernames, maxResults }) }
  );
  // waitForFinish caps at 60s per call and returns a still-RUNNING run when
  // it expires, so keep waiting rather than mistaking that for a failure.
  while (run.status === "RUNNING" || run.status === "READY") {
    ({ data: run } = await apiFetch(
      `/actor-runs/${run.id}?waitForFinish=60`,
      token
    ));
  }
  if (run.status !== "SUCCEEDED") {
    throw new Error(`run finished with status ${run.status}`);
  }

  // Tolerate a missing OUTPUT (404) rather than failing the whole scrape:
  // the record is only absent on runs older than the actor build that
  // introduced it.
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
const stories = await scrapeStories(usernames.length ? usernames : ["natgeo"]);

console.log(`${stories.length} active stories`);
for (const s of stories) {
  console.log(
    `@${s.username} [${s.media_type}] posted ${s.taken_at}, expires ${s.expiring_at}`
  );
}
