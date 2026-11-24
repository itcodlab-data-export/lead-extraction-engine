import { useState } from "preact/hooks";
import { roas } from "../lib/roas";

const num = (v: string) => (Number.isFinite(parseFloat(v)) ? parseFloat(v) : 0);
const fmt = (n: number | null, d = 2) => (n === null ? "—" : n.toLocaleString(undefined, { maximumFractionDigits: d }));

export default function RoasCalc() {
  const [v, setV] = useState({ spend: "1000", purchases: "20", aov: "100", margin: "40" });
  const set = (k: string) => (e: Event) => setV({ ...v, [k]: (e.target as HTMLInputElement).value });
  const r = roas({ spend: num(v.spend), purchases: num(v.purchases), aov: num(v.aov), marginPct: num(v.margin) });
  const below = r.profit !== null && r.profit < 0;
  const fields: [string, string, string][] = [
    ["spend", "Ad spend", "any currency"], ["purchases", "Purchases", "count"],
    ["aov", "Average order value", "same currency"], ["margin", "Gross margin %", "before ad spend"],
  ];
  const rows: [string, string][] = [
    ["ROAS", fmt(r.roas)], ["Break-even ROAS", fmt(r.beRoas)],
    ["Your CPA", fmt(r.cpa)], ["Break-even CPA", fmt(r.beCpa)], ["Profit after ads", fmt(r.profit, 0)],
  ];
  return (
    <div class="grid gap-8 md:grid-cols-2">
      <form class="grid gap-4" onSubmit={(e) => e.preventDefault()}>
        <p class="font-mono text-xs text-ink-2">Illustrative starting inputs — replace with your own numbers.</p>
        {fields.map(([k, label, hint]) => (
          <label class="grid gap-1 text-sm font-semibold">{label} <span class="font-normal text-ink-2">({hint})</span>
            <input class="field" inputMode="decimal" value={v[k as keyof typeof v]} onInput={set(k)} /></label>
        ))}
      </form>
      <div aria-live="polite">
        <span class="badge">{below && <span class="dot-live" aria-hidden="true" />}
          {r.profit === null ? "Enter spend and margin" : below ? "Below break-even" : "At or above break-even"}</span>
        <dl class="mt-4 bg-surface p-4 font-mono text-sm" style="border-radius:4px">
          {rows.map(([k, val]) => (
            <div class="flex justify-between border-b border-hairline py-3 last:border-0"><dt class="text-ink-2">{k}</dt><dd>{val}</dd></div>
          ))}
        </dl>
      </div>
    </div>
  );
}
