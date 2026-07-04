"use client";

import type { RiskFactor } from "../lib/analysis";

type RiskFactorSelectorProps = {
  factors: RiskFactor[];
  selectedIds: Set<number>;
  onToggle: (id: number) => void;
};

/** Short preview text for a factor: its client-facing summary, else an excerpt. */
function preview(factor: RiskFactor): string {
  const text = factor.summary?.trim() || factor.verbatim_text;
  const collapsed = text.replace(/\s+/g, " ").trim();
  return collapsed.length > 240 ? `${collapsed.slice(0, 240)}…` : collapsed;
}

export default function RiskFactorSelector({
  factors,
  selectedIds,
  onToggle,
}: RiskFactorSelectorProps) {
  return (
    <ul className="flex flex-col gap-3">
      {factors.map((factor) => {
        const checked = selectedIds.has(factor.id);
        return (
          <li key={factor.id}>
            <label
              className={`flex cursor-pointer items-start gap-3 rounded-sm border p-4 transition-colors ${
                checked
                  ? "border-accent-primary bg-accent-primary/10"
                  : "border-border-default bg-bg-surface hover:border-border-subtle"
              }`}
            >
              <input
                type="checkbox"
                checked={checked}
                onChange={() => onToggle(factor.id)}
                className="mt-1 h-4 w-4 shrink-0 accent-accent-primary"
              />
              <div className="flex min-w-0 flex-col gap-1.5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-semibold text-text-primary">
                    {factor.title}
                  </span>
                  {factor.category ? (
                    <span className="rounded-sm border border-border-default px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-text-secondary">
                      {factor.category}
                    </span>
                  ) : null}
                </div>
                <p className="text-sm leading-relaxed text-text-secondary">
                  {preview(factor)}
                </p>
              </div>
            </label>
          </li>
        );
      })}
    </ul>
  );
}
