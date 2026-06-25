const PILLS = [
  "LLM-as-judge eval pipeline",
  "Hybrid BM25 + semantic retrieval",
  "Citation-grounded outputs",
];

export default function FeaturePills() {
  return (
    <div className="flex flex-wrap items-center justify-center gap-3">
      {PILLS.map((pill) => (
        <span
          key={pill}
          className="rounded-sm border border-border-subtle bg-bg-secondary/40 px-3 py-1.5 font-mono text-xs text-text-muted"
        >
          {pill}
        </span>
      ))}
    </div>
  );
}
