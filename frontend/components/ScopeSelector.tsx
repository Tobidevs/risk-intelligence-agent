"use client";

type ScopeSelectorProps = {
  scopeMDA: boolean;
  scopeCrossRef: boolean;
  onToggleMDA: () => void;
  onToggleCrossRef: () => void;
};

const LockIcon = () => (
  <svg
    className="h-3 w-3"
    viewBox="0 0 20 20"
    fill="currentColor"
    aria-hidden="true"
  >
    <path
      fillRule="evenodd"
      d="M10 1a4 4 0 0 0-4 4v2H5a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-1V5a4 4 0 0 0-4-4Zm2 6V5a2 2 0 1 0-4 0v2h4Z"
      clipRule="evenodd"
    />
  </svg>
);

const activeChip =
  "border-accent-primary bg-accent-primary/10 text-accent-primary";
const inactiveChip = "border-border-subtle text-text-muted hover:border-border-default";

function buildSummary(scopeMDA: boolean, scopeCrossRef: boolean): string {
  const sections = ["Risk Factors"];
  if (scopeMDA) sections.push("MD&A");

  const sectionText =
    sections.length === 1
      ? sections[0]
      : `${sections.slice(0, -1).join(", ")} and ${sections[sections.length - 1]}`;

  const suffix = scopeCrossRef ? " with cross-section correlation" : "";
  return `Analyzing ${sectionText}${suffix}.`;
}

export default function ScopeSelector({
  scopeMDA,
  scopeCrossRef,
  onToggleMDA,
  onToggleCrossRef,
}: ScopeSelectorProps) {
  return (
    <div className="flex flex-col gap-2">
      <span className="font-mono text-xs uppercase tracking-widest text-text-muted">
        Analysis Scope
      </span>

      <div className="flex flex-wrap gap-2">
        {/* Risk Factors — always active, locked */}
        <button
          type="button"
          disabled
          className={`flex cursor-not-allowed items-center gap-2 rounded-sm border px-3 py-2 font-mono text-xs ${activeChip}`}
        >
          <LockIcon />
          Risk Factors (Item 1A)
        </button>

        {/* MD&A — toggleable */}
        <button
          type="button"
          onClick={onToggleMDA}
          aria-pressed={scopeMDA}
          className={`rounded-sm border px-3 py-2 font-mono text-xs transition-colors ${
            scopeMDA ? activeChip : inactiveChip
          }`}
        >
          MD&A (Item 7)
        </button>

        {/* Cross-Reference — toggleable, dimmed label + tooltip */}
        <div className="group relative">
          <button
            type="button"
            onClick={onToggleCrossRef}
            aria-pressed={scopeCrossRef}
            className={`rounded-sm border px-3 py-2 font-mono text-xs opacity-90 transition-colors ${
              scopeCrossRef ? activeChip : inactiveChip
            }`}
          >
            Cross-Reference Analysis
          </button>
          <span
            role="tooltip"
            className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 w-64 -translate-x-1/2 rounded-sm border border-border-default bg-bg-elevated px-3 py-2 text-center font-mono text-[11px] leading-relaxed text-text-secondary opacity-0 shadow-lg transition-opacity duration-150 group-hover:opacity-100"
          >
            Correlates risk language in Item 1A against operational evidence in
            Item 7
          </span>
        </div>
      </div>

      <p className="font-mono text-xs text-text-muted">
        {buildSummary(scopeMDA, scopeCrossRef)}
      </p>
    </div>
  );
}
