// Cloudflare Worker: form intake. Verify Turnstile -> Neon (atomic) -> ntfy (zero PII).
// Secrets: TURNSTILE_SECRET, DATABASE_URL, NTFY_TOPIC. Var: ALLOWED_ORIGINS (comma list).
const FREE_MAIL = new Set(["gmail.com", "googlemail.com", "yahoo.com", "outlook.com", "hotmail.com", "live.com", "icloud.com", "proton.me", "protonmail.com", "aol.com", "rediffmail.com"]);
const clip = (v, n) => String(v ?? "").trim().slice(0, n);

export default {
  async fetch(req, env, ctx) {
    const origin = req.headers.get("origin") || "";
    const allowed = (env.ALLOWED_ORIGINS || "").split(",").map((s) => s.trim());
    const cors = {
      "access-control-allow-origin": allowed.includes(origin) ? origin : allowed[0] || "",
      "access-control-allow-methods": "POST, OPTIONS",
      "access-control-allow-headers": "content-type",
      vary: "origin",
    };
    const reply = (status, ok) => new Response(JSON.stringify({ ok }), { status, headers: { ...cors, "content-type": "application/json" } });
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    if (req.method !== "POST" || !allowed.includes(origin)) return reply(403, false);

    let b;
    try { b = await req.json(); } catch { return reply(400, false); }
    if (b.website) return reply(200, true); // honeypot: pretend success
    const email = clip(b.email, 200).toLowerCase();
    const name = clip(b.name, 120);
    if (!name || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return reply(422, false);

    const form = new FormData();
    form.set("secret", env.TURNSTILE_SECRET);
    form.set("response", clip(b["cf-turnstile-response"], 2048));
    form.set("remoteip", req.headers.get("cf-connecting-ip") || "");
    const v = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", { method: "POST", body: form });
    if (!(await v.json()).success) return reply(403, false);

    const domain = email.split("@")[1];
    const queries = [{
      query: "insert into website_inquiries (name,email,company,interest,message,source,domain) values ($1,$2,$3,$4,$5,$6,$7)",
      params: [name, email, clip(b.company, 160), clip(b.interest, 80), clip(b.message, 2000), clip(b.source, 40), domain],
    }];
    if (!FREE_MAIL.has(domain)) {
      queries.push({
        query: "insert into suppression_list (scope,value,reason) values ('DOMAIN',$1,'INBOUND_WEBSITE_LEAD') on conflict (scope,value) do nothing",
        params: [domain],
      });
    }
    // Neon HTTP SQL: `queries` run as a single transaction (atomic).
    const host = new URL(env.DATABASE_URL).hostname;
    const db = await fetch(`https://${host}/sql`, {
      method: "POST",
      headers: { "content-type": "application/json", "Neon-Connection-String": env.DATABASE_URL },
      body: JSON.stringify({ queries }),
    });
    if (!db.ok) return reply(502, false);

    ctx.waitUntil(fetch(`https://ntfy.sh/${env.NTFY_TOPIC}`, {
      method: "POST",
      headers: { Priority: "5", Title: "New website inquiry", Tags: "bell" },
      body: `Source: ${clip(b.source, 40) || "web"}. Open the database to view.`, // no PII
    }));
    return reply(200, true);
  },
};
