import type { APIRoute } from "astro";
import { isProduction, SITE } from "../lib/site";
import { withBase } from "../lib/withBase";

export const GET: APIRoute = () => {
  const body = isProduction
    ? ["User-agent: *", "Allow: /", "", "User-agent: Googlebot", "Allow: /", "", "User-agent: OAI-SearchBot", "Allow: /", "",
       "User-agent: PerplexityBot", "Allow: /", "", `Sitemap: ${SITE}${withBase("/sitemap-index.xml")}`]
    : ["# Staging build — not for indexing", "User-agent: *", "Disallow: /"];
  return new Response(body.join("\n") + "\n", { headers: { "content-type": "text/plain; charset=utf-8" } });
};
