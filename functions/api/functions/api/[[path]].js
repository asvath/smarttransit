// /functions/api/[[path]].js
// This Cloudflare Pages Function proxies any /api/* request
// to your existing Worker (leaderboard-api.ashaasvathaman.workers.dev).

const WORKER_BASE = "https://leaderboard-api.ashaasvathaman.workers.dev";

function upstreamUrl(request) {
  const inUrl = new URL(request.url);
  // Remove the leading "/api/" part from the path.
  const stripped = inUrl.pathname.replace(/^\/api\/?/, ""); // e.g. "leaderboard"
  const qs = inUrl.search ? inUrl.search : "";
  return `${WORKER_BASE}/${stripped}${qs}`;
}

export async function onRequestOptions() {
  // Handle browser preflight (CORS) requests quickly.
  return new Response(null, { status: 204 });
}

export async function onRequest({ request }) {
  const method = request.method;
  const url = upstreamUrl(request);

  let init = { method };

  if (method !== "GET" && method !== "HEAD") {
    // Forward POST/PUT bodies too.
    const body = await request.text();
    init.body = body;
    const hdrs = new Headers(request.headers);
    if (!hdrs.get("content-type")) hdrs.set("content-type", "application/json");
    init.headers = hdrs;
  } else {
    // For GET requests, disable caching.
    init.headers = { "cache-control": "no-store" };
  }

  // Fetch from the real Worker
  const r = await fetch(url, init);

  // Copy headers and force "no-store"
  const outHeaders = new Headers(r.headers);
  if (!outHeaders.get("content-type"))
    outHeaders.set("content-type", "application/json; charset=utf-8");
  outHeaders.set("cache-control", "no-store, no-cache, must-revalidate, max-age=0");
  outHeaders.set("pragma", "no-cache");
  outHeaders.set("expires", "0");
  outHeaders.set("cdn-cache-control", "no-store");

  // Return the response back to the browser
  return new Response(r.body, { status: r.status, headers: outHeaders });
}
