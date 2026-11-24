/** Single source of truth for site constants. No secrets. */
import { withBase } from "./withBase";

export const SITE = (import.meta.env.SITE || "https://itcodlab.com").replace(/\/+$/, "");
export const isProduction = ["itcodlab.com", "www.itcodlab.com"].includes(new URL(SITE).hostname);
export const BUILT_AT = new Date().toISOString();

export const BRAND = "IT Code Lab";
export const TAGLINE = "AI-powered performance marketing, social growth and IT automation.";
export const APP_URL = "https://app.itcodlab.com";
/** Fill when real profiles exist. Empty = omitted from JSON-LD (no phantom markup). */
export const SAME_AS: string[] = [];

export const FORM_ENDPOINT = import.meta.env.PUBLIC_FORM_ENDPOINT || "";
export const TURNSTILE_KEY =
  import.meta.env.PUBLIC_TURNSTILE_SITE_KEY || (isProduction ? "" : "1x00000000000000000000AA");
export const CAL_LINK = import.meta.env.PUBLIC_CAL_LINK || "";
export const CF_ANALYTICS_TOKEN = import.meta.env.PUBLIC_CF_ANALYTICS_TOKEN || "";

/** Absolute canonical URL (base-aware). */
export const abs = (path: string) => new URL(withBase(path), SITE + "/").href;

export const NAV = [
  { label: "Services", href: "/services/" },
  { label: "Products", href: "/products/" },
  { label: "Lab", href: "/lab/" },
  { label: "About", href: "/about/" },
];
