import type { APIRoute } from "astro";
import { getCollection } from "astro:content";
import { abs, BRAND, TAGLINE } from "../lib/site";

export const GET: APIRoute = async () => {
  const line = (t: string, p: string, d: string) => `- [${t}](${abs(p)}): ${d}`;
  const section = async (title: string, name: "services" | "products") => {
    const items = (await getCollection(name)).sort((a, b) => a.data.order - b.data.order);
    return [`## ${title}`, ...items.map((e) => line(e.data.title, `/${name}/${e.id}/`, e.data.description)), ""];
  };
  const out = [
    `# ${BRAND}`, "", `> ${TAGLINE}`, "",
    ...(await section("Services", "services")), ...(await section("Products", "products")),
    "## Pages",
    line("Home", "/", "Overview of services and products"),
    line("About", "/about/", "Founder and approach"),
    line("Lab", "/lab/", "Free Meta Ads ROAS and break-even CPA calculator"),
    line("Contact", "/contact/", "Inquiry form and booking"),
    line("Early access", "/early-access/", "Join the client portal waitlist"),
    line("Privacy Policy", "/privacy-policy/", "DPDP and GDPR disclosures"),
    line("Terms", "/terms/", "Terms of use"), "",
  ];
  return new Response(out.join("\n"), { headers: { "content-type": "text/plain; charset=utf-8" } });
};
