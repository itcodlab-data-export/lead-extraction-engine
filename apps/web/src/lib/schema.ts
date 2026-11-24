/** JSON-LD @graph builders. Every field must have a visible-HTML counterpart. */
import { SITE, BRAND, SAME_AS, BUILT_AT, abs } from "./site";

export const ORG_ID = `${SITE}/#organization`;
const SITE_ID = `${SITE}/#website`;

export const organization = () => ({
  "@type": "Organization",
  "@id": ORG_ID,
  name: BRAND,
  url: abs("/"),
  description: "Performance marketing (Meta Ads + server-side CAPI), social media growth and IT automation agency.",
  ...(SAME_AS.length ? { sameAs: SAME_AS } : {}),
});

export const website = () => ({
  "@type": "WebSite",
  "@id": SITE_ID,
  url: abs("/"),
  name: BRAND,
  publisher: { "@id": ORG_ID },
});

export const breadcrumbs = (trail: { name: string; path: string }[]) => ({
  "@type": "BreadcrumbList",
  itemListElement: trail.map((t, i) => ({
    "@type": "ListItem",
    position: i + 1,
    name: t.name,
    item: abs(t.path),
  })),
});

export const webPage = (o: { path: string; title: string; description: string; type?: string; speakable?: boolean }) => ({
  "@type": o.type || "WebPage",
  "@id": `${abs(o.path)}#webpage`,
  url: abs(o.path),
  name: o.title,
  description: o.description,
  isPartOf: { "@id": SITE_ID },
  dateModified: BUILT_AT,
  ...(o.speakable === false ? {} : { speakable: { "@type": "SpeakableSpecification", cssSelector: [".speakable"] } }),
});

export const service = (name: string, description: string, path: string) => ({
  "@type": "Service",
  name,
  description,
  url: abs(path),
  provider: { "@id": ORG_ID },
});

export const software = (name: string, description: string, path: string) => ({
  "@type": "SoftwareApplication",
  name,
  description,
  url: abs(path),
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web",
  publisher: { "@id": ORG_ID },
});

export const faqPage = (items: { q: string; a: string }[]) => ({
  "@type": "FAQPage",
  mainEntity: items.map((i) => ({
    "@type": "Question",
    name: i.q,
    acceptedAnswer: { "@type": "Answer", text: i.a },
  })),
});

export const person = (name: string, jobTitle: string, description: string, path: string) => ({
  "@type": "Person",
  "@id": `${SITE}/#founder`,
  name,
  jobTitle,
  description,
  url: abs(path),
  worksFor: { "@id": ORG_ID },
});
