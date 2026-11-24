// Post-build HTML audit: JSON-LD validity, internal links, llms.txt, robots/noindex, FAQ word counts.
// Usage: BASE_PATH=/x/ SITE_URL=... node scripts/audit.mjs   (reads ./dist)
import { readdirSync, readFileSync, existsSync, statSync } from "node:fs";
import { join } from "node:path";

const DIST = "dist";
const BASE = `/${(process.env.BASE_PATH || "/").replace(/^\/+|\/+$/g, "")}/`.replace("//", "/");
const PROD = /^https:\/\/(www\.)?itcodlab\.com\/?$/.test(process.env.SITE_URL || "https://itcodlab.com");
const fails = [];
const fail = (mod, err, line = "-") => fails.push(`[FAIL] ${mod} | ${err} | ${line}`);

const walk = (d) => readdirSync(d).flatMap((f) => (statSync(join(d, f)).isDirectory() ? walk(join(d, f)) : [join(d, f)]));
const exists = (url) => {
  const p = decodeURI(url.split(/[?#]/)[0]);
  if (!p.startsWith(BASE)) return false;
  const rel = p.slice(BASE.length);
  const f = join(DIST, rel);
  return existsSync(f) && statSync(f).isFile() ? true : existsSync(join(f, "index.html"));
};

const pages = walk(DIST).filter((f) => f.endsWith(".html"));
if (!pages.length) fail("audit", "no html pages in dist", DIST);

for (const file of pages) {
  const html = readFileSync(file, "utf8");
  const ld = [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)];
  if (ld.length !== 1) fail(file, `expected 1 JSON-LD block, found ${ld.length}`, "head");
  else {
    try {
      const j = JSON.parse(ld[0][1]);
      const g = j["@graph"];
      if (!Array.isArray(g)) fail(file, "JSON-LD has no @graph array", "head");
      else {
        const ids = g.map((n) => n["@id"]).filter(Boolean);
        if (new Set(ids).size !== ids.length) fail(file, "duplicate @id in @graph", "head");
        const types = g.map((n) => n["@type"]);
        if (g.some((n) => n.speakable) && !html.includes('class="speakable') && !/class="[^"]*\bspeakable\b/.test(html))
          fail(file, "Speakable declared but no .speakable element", "body");
        if (types.includes("FAQPage")) {
          for (const q of g.find((n) => n["@type"] === "FAQPage").mainEntity) {
            const words = q.acceptedAnswer.text.trim().split(/\s+/).length;
            if (words < 40 || words > 60) fail(file, `FAQ answer ${words} words (need 40-60)`, q.name.slice(0, 30));
            if (!html.includes(q.acceptedAnswer.text)) fail(file, "FAQ answer not visible in static HTML", q.name.slice(0, 30));
          }
        }
      }
    } catch (e) { fail(file, `invalid JSON-LD (${e.name})`, "head"); }
  }
  const robots = /<meta name="robots" content="([^"]+)"/.exec(html)?.[1] || "";
  if (!PROD && !robots.includes("noindex")) fail(file, "staging build missing noindex", "head");
  if (PROD && robots.includes("noindex")) fail(file, "production build has noindex", "head");
  if (/<details[^>]*>[^]*?<summary[^>]*>[^<]*\?/.test(html)) fail(file, "FAQ-like accordion found", "body");

  for (const m of html.matchAll(/\s(?:href|src)="([^"]+)"/g)) {
    const u = m[1];
    if (/^(https?:|mailto:|tel:|data:|#|\/\/)/.test(u)) continue;
    if (!u.startsWith("/")) { fail(file, "relative URL (not base-prefixed)", u); continue; }
    if (!u.startsWith(BASE) && BASE !== "/") fail(file, "missing base prefix", u);
    else if (!exists(u)) fail(file, "broken internal link", u);
  }
}

const must = ["llms.txt", "robots.txt", "sitemap-index.xml", "404.html", "favicon.svg"];
for (const f of must) if (!existsSync(join(DIST, f))) fail("dist", "missing output file", f);
if (existsSync(join(DIST, "llms.txt"))) {
  const t = readFileSync(join(DIST, "llms.txt"), "utf8");
  if (!t.startsWith("# ") || !t.includes("## Services") || !t.includes("## Products")) fail("llms.txt", "missing expected sections", "1");
}
if (existsSync(join(DIST, "robots.txt"))) {
  const r = readFileSync(join(DIST, "robots.txt"), "utf8");
  if (PROD !== r.includes("OAI-SearchBot")) fail("robots.txt", PROD ? "prod missing allow rules" : "staging must disallow all", "1");
}

if (fails.length) { console.error(fails.slice(0, 20).join("\n")); process.exit(1); }
console.log(`[OK] audit | ${pages.length} pages | base=${BASE} ${PROD ? "production" : "staging"}`);
