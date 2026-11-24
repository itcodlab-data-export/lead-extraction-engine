export interface RoasInput { spend: number; purchases: number; aov: number; marginPct: number }

/** Pure maths for the Lab calculator. Returns null fields when inputs are not usable. */
export function roas({ spend, purchases, aov, marginPct }: RoasInput) {
  const m = marginPct / 100;
  const revenue = purchases * aov;
  const ok = spend > 0 && m > 0;
  return {
    revenue,
    roas: spend > 0 ? revenue / spend : null,
    cpa: purchases > 0 ? spend / purchases : null,
    beRoas: m > 0 ? 1 / m : null,
    beCpa: aov > 0 && m > 0 ? aov * m : null,
    profit: ok ? revenue * m - spend : null,
  };
}
