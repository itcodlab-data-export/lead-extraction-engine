/** Architecture previews for the home sandbox. Descriptive only — no performance claims. */
export interface Tab {
  id: string;
  label: string;
  title: string;
  status: string;
  live: boolean;
  steps: string[];
  specs: [string, string][];
}

export const TABS: Tab[] = [
  {
    id: "ads", label: "Performance Ads", title: "Meta Ads with server-side CAPI", status: "Service", live: true,
    steps: ["Browser pixel event", "Server-side CAPI event", "Deduplicate by event_id", "Meta optimisation signal"],
    specs: [["events", "Purchase · Lead · AddToCart"], ["dedup", "event_id match"], ["match", "hashed first-party data"]],
  },
  {
    id: "social", label: "Social Media", title: "Social growth, run as a system", status: "Service", live: true,
    steps: ["Content pillars", "Weekly publishing cadence", "Community replies", "Performance review"],
    specs: [["channels", "chosen per account"], ["cadence", "planned per account"], ["reporting", "agreed per account"]],
  },
  {
    id: "extract", label: "Lead Extraction", title: "Lead Extraction Engine", status: "In-house product", live: true,
    steps: ["14 intent sources", "Dedup against master index", "Email verification", "Google Sheet output"],
    specs: [["sources", "14"], ["sheet", "5 tabs × 24 columns"], ["run", "daily, scheduled"]],
  },
  {
    id: "send", label: "Lead Sending", title: "Lead Sending Engine", status: "In development", live: false,
    steps: ["Suppression check", "Immutable daily ceilings", "Fail-closed counter", "Sequenced sending"],
    specs: [["safety layers", "9"], ["on counter error", "skip sending"], ["availability", "early access"]],
  },
  {
    id: "it", label: "IT & AI", title: "IT and AI automation", status: "Service", live: true,
    steps: ["Trigger", "Serverless worker", "Database write", "Instant alert"],
    specs: [["runtime", "Cloudflare Workers"], ["database", "Postgres"], ["alerts", "ntfy, no personal data"]],
  },
];
