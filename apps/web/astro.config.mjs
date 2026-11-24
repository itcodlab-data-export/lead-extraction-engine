import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";
import preact from "@astrojs/preact";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";

// Normalise "/x", "x/" -> "/x/" so `base` is correct on GitHub Pages subpath AND root hosting.
const base = `/${(process.env.BASE_PATH || "/").replace(/^\/+|\/+$/g, "")}/`.replace("//", "/");

export default defineConfig({
  site: process.env.SITE_URL || "https://itcodlab.com",
  base,
  output: "static",
  trailingSlash: "always",
  build: { format: "directory" },
  integrations: [
    tailwind({ applyBaseStyles: false }),
    preact(),
    mdx(),
    sitemap({ filter: (page) => !page.endsWith("/404/") }),
  ],
});
