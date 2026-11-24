/** Shared Tailwind preset — consumed by apps/web (Astro) and apps/portal (Next.js, PR #3). */
const v = (name) => `var(--${name})`;

/** @type {import('tailwindcss').Config} */
export default {
  theme: {
    extend: {
      colors: {
        canvas: v("bg-canvas"),
        surface: v("bg-surface"),
        glass: v("glass-bg"),
        hairline: v("border-hairline"),
        ink: v("text-primary"),
        "ink-2": v("text-secondary"),
        brand: v("accent-blue"),
        signal: v("accent-red"),
      },
      fontFamily: {
        sans: [v("font-sans")],
        display: [v("font-display")],
        mono: [v("font-mono")],
      },
      maxWidth: { container: v("container") },
      spacing: { section: v("section-y"), gutter: v("gutter") },
      letterSpacing: { display: "-0.03em" },
      lineHeight: { display: "1.05" },
      keyframes: {
        pulseDot: { "0%,100%": { opacity: "1" }, "50%": { opacity: "0.35" } },
      },
      animation: { "pulse-dot": "pulseDot 2s ease-in-out infinite" },
    },
  },
};
