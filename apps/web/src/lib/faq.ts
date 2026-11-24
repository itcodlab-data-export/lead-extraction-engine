/** AEO FAQ — one source for visible HTML and FAQPage JSON-LD. Answers: 40–60 words each. */
export const FAQ = [
  {
    q: "What is server-side Conversions API (CAPI) and why does my Meta ads account need it?",
    a: "Server-side CAPI sends purchase and lead events from your server directly to Meta instead of relying only on the browser pixel. Browsers and ad blockers drop pixel events, so Meta sees fewer conversions. Sending the same events from the server, deduplicated by event ID, gives the ad algorithm more complete signal to optimise against.",
  },
  {
    q: "How does IT Code Lab protect my sending domain's reputation?",
    a: "Our Lead Sending Engine is designed around a nine-layer inbox safety barrier: verification, suppression checks, fixed daily ceilings and fail-closed behaviour. If a safety counter cannot be read, sending is skipped rather than guessed. The goal is to keep volume conservative so your domain reputation is not put at risk.",
  },
  {
    q: "Who owns the data that the Lead Extraction Engine collects?",
    a: "You do. The Lead Extraction Engine writes its output into a Google Sheet that you control, with records deduplicated against a master index inside that same sheet. Nothing is saved as exported CSV files, and credentials live only in encrypted deployment secrets rather than in code, so the data stays in your own workspace.",
  },
  {
    q: "Is your lead extraction compliant with DPDP, CAN-SPAM and PECR?",
    a: "We build around these rules: business-contact focus, honoured opt-outs, suppression lists and clear sender identity. Compliance also depends on how and where you use the data, so this is not legal advice. We recommend confirming your specific campaigns with a qualified adviser for India's DPDP Act, the US CAN-SPAM Act and UK PECR.",
  },
  {
    q: "What happens in the free audit?",
    a: "You book a call and we review how your Meta ads tracking is set up, including pixel and server-side events, plus your current funnel and any automation gaps. You leave knowing what is working, what is leaking signal and what to fix first. The audit is free, and booking it does not commit you to hiring us for anything afterwards.",
  },
];
