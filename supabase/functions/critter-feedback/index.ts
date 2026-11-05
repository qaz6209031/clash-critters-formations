// Receives feedback from the static critterformations.com pages and stores it in
// public.critter_feedback. The site is static (GitHub Pages), so this function plays the
// role of a server-side /api/feedback route: the browser never talks to the database, and
// the service-role key only exists here.
//
// Deploy: supabase functions deploy critter-feedback --project-ref njzrhztlmvhcpjglnuut --no-verify-jwt --use-api
// Limits mirror the check constraints in supabase/sql/critter_feedback.sql; keep them in sync.
// Error codes are mapped to translated messages by the form (FEEDBACK_STRINGS in stage-47/build_site.py).

const MAX_MESSAGE_LENGTH = 2000;
const MAX_EMAIL_LENGTH = 320;
const MAX_PAGE_LENGTH = 200;
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const LANGS = new Set(["en", "zh-hant", "ko", "vi"]);
const DEFAULT_ORIGINS =
  "https://critterformations.com,https://www.critterformations.com,http://127.0.0.1:8047,http://localhost:8047";
const ALLOWED_ORIGINS = new Set(
  (Deno.env.get("ALLOWED_ORIGINS") ?? DEFAULT_ORIGINS).split(",").map((o) => o.trim()).filter(Boolean),
);

// Best-effort per-IP limit. In-memory, so it only holds within one function instance.
const RATE_LIMIT = 5;
const RATE_WINDOW_MS = 60_000;
const recentHits = new Map<string, number[]>();

function isRateLimited(ip: string): boolean {
  const now = Date.now();
  const hits = (recentHits.get(ip) ?? []).filter((t) => now - t < RATE_WINDOW_MS);
  hits.push(now);
  recentHits.set(ip, hits);
  if (recentHits.size > 5000) recentHits.clear();
  return hits.length > RATE_LIMIT;
}

function corsHeaders(origin: string): Record<string, string> {
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "content-type",
    "Access-Control-Max-Age": "86400",
    Vary: "Origin",
  };
}

function json(body: unknown, status: number, origin: string): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders(origin), "Content-Type": "application/json" },
  });
}

function optionalString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

async function saveFeedback(row: Record<string, unknown>): Promise<void> {
  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!supabaseUrl || !serviceKey) throw new Error("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set");
  const headers: Record<string, string> = {
    apikey: serviceKey,
    "Content-Type": "application/json",
    Prefer: "return=minimal",
  };
  // Legacy service-role keys are JWTs and also go in Authorization; sb_secret_ keys do not.
  if (serviceKey.startsWith("eyJ")) headers.Authorization = `Bearer ${serviceKey}`;
  const res = await fetch(`${supabaseUrl}/rest/v1/critter_feedback`, {
    method: "POST",
    headers,
    body: JSON.stringify(row),
  });
  if (!res.ok) throw new Error(`Supabase insert failed: ${res.status} ${await res.text()}`);
}

Deno.serve(async (req) => {
  const origin = req.headers.get("origin") ?? "";
  if (!ALLOWED_ORIGINS.has(origin)) {
    return new Response(JSON.stringify({ error: "forbidden" }), {
      status: 403,
      headers: { "Content-Type": "application/json" },
    });
  }
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders(origin) });
  if (req.method !== "POST") return json({ error: "method_not_allowed" }, 405, origin);

  const ip = (req.headers.get("x-forwarded-for") ?? "").split(",")[0].trim() || "unknown";
  if (isRateLimited(ip)) return json({ error: "rate_limited" }, 429, origin);

  let body: Record<string, unknown>;
  try {
    const parsed = await req.json();
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) throw new Error("not an object");
    body = parsed;
  } catch {
    return json({ error: "bad_request" }, 400, origin);
  }

  // Honeypot: real visitors never see or fill the "website" field.
  if (body.website) return json({ ok: true }, 200, origin);

  const rating = body.rating === null || body.rating === undefined ? null : body.rating;
  if (rating !== null && !(Number.isInteger(rating) && (rating as number) >= 1 && (rating as number) <= 5)) {
    return json({ error: "invalid_rating" }, 400, origin);
  }

  const message = optionalString(body.message);
  if (message && message.length > MAX_MESSAGE_LENGTH) return json({ error: "message_too_long" }, 400, origin);

  const email = optionalString(body.email);
  if (email && (email.length > MAX_EMAIL_LENGTH || !EMAIL_REGEX.test(email))) {
    return json({ error: "invalid_email" }, 400, origin);
  }

  if (rating === null && !message) return json({ error: "empty" }, 400, origin);

  const rawPage = optionalString(body.page);
  const page = rawPage && rawPage.startsWith("/") ? rawPage.slice(0, MAX_PAGE_LENGTH) : null;
  const lang = typeof body.lang === "string" && LANGS.has(body.lang) ? body.lang : null;

  try {
    await saveFeedback({ rating, message, email, page, lang });
  } catch (e) {
    console.error("Failed to save feedback", e);
    return json({ error: "server" }, 500, origin);
  }
  return json({ ok: true }, 200, origin);
});
