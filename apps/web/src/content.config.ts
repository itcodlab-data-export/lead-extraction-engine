import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

/** Add one .mdx to a folder => a new page, sitemap entry and llms.txt line. No code changes. */
const base = z.object({
  title: z.string(),
  description: z.string().max(200),
  order: z.number().default(100),
});
const make = (dir: string, extra: z.ZodRawShape = {}) =>
  defineCollection({
    loader: glob({ pattern: "**/*.{md,mdx}", base: `./src/content/${dir}` }),
    schema: base.extend(extra),
  });

export const collections = {
  services: make("services"),
  products: make("products", { status: z.enum(["live", "in-development", "early-access"]).default("early-access") }),
  blog: make("blog", { published: z.coerce.date() }),
  "case-studies": make("case-studies", { published: z.coerce.date() }),
};
