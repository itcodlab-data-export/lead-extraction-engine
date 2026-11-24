import { useState } from "preact/hooks";
import { TABS } from "./sandboxData";

export default function TabSandbox() {
  const [i, setI] = useState(0);
  const t = TABS[i];
  const onKey = (e: KeyboardEvent) => {
    if (e.key === "ArrowRight") setI((i + 1) % TABS.length);
    if (e.key === "ArrowLeft") setI((i + TABS.length - 1) % TABS.length);
  };
  return (
    <div>
      <div role="tablist" aria-label="Capabilities" onKeyDown={onKey}
        class="-mx-1 flex gap-1 overflow-x-auto border-b border-hairline pb-3">
        {TABS.map((x, n) => (
          <button role="tab" id={`tab-${x.id}`} aria-selected={n === i} aria-controls="sandbox-panel"
            tabIndex={n === i ? 0 : -1} onClick={() => setI(n)}
            class={`shrink-0 rounded-full px-4 py-2 text-sm font-semibold ${n === i ? "bg-brand text-white" : "text-ink-2 hover:bg-surface"}`}
            style="min-height:44px">{x.label}</button>
        ))}
      </div>
      <div role="tabpanel" id="sandbox-panel" aria-labelledby={`tab-${t.id}`} class="pt-6">
        <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
          <h3 class="text-xl">{t.title}</h3>
          <span class="badge">{t.live && <span class="dot-live" aria-hidden="true" />}{t.status}</span>
        </div>
        <div class="grid gap-6 md:grid-cols-[1.4fr_1fr]">
          <ol class="space-y-2">
            {t.steps.map((s, n) => (
              <li class="flex items-center gap-3 rounded border border-hairline bg-canvas px-4 py-3 text-sm">
                <span class="font-mono text-xs text-brand">{String(n + 1).padStart(2, "0")}</span>{s}
              </li>
            ))}
          </ol>
          <dl class="bg-surface p-4 font-mono text-xs" style="border-radius:4px">
            {t.specs.map(([k, v]) => (
              <div class="flex justify-between gap-4 border-b border-hairline py-2 last:border-0">
                <dt class="text-ink-2">{k}</dt><dd class="text-right text-ink">{v}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </div>
  );
}
