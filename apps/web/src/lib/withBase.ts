/** Prefix internal paths with Astro's BASE_URL (GitHub Pages subpath OR root hosting). */
const BASE = (import.meta.env.BASE_URL || "/").replace(/\/+$/, "");

export function withBase(path: string): string {
  if (/^([a-z][a-z0-9+.-]*:|\/\/|#)/i.test(path)) return path; // external / hash-only
  const m = path.match(/^([^?#]*)(.*)$/)!;
  let p = "/" + m[1].replace(/^\/+/, "");
  if (!p.endsWith("/") && !/\.[a-z0-9]+$/i.test(p)) p += "/"; // directory-format pages
  return BASE + p + m[2];
}
