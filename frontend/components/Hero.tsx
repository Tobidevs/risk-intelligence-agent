import AnalysisForm from "./AnalysisForm";
import FeaturePills from "./FeaturePills";
import StatusDate from "./StatusDate";

export default function Hero() {
  return (
    <div className="relative flex min-h-screen flex-col">
      {/* Terminal status bar */}
      <div className="flex items-center justify-between border-b border-border-subtle px-4 py-2.5 font-mono text-[11px] uppercase tracking-widest text-text-muted">
        <span>FilingLens v0.1 Beta</span>
        <StatusDate />
      </div>

      {/* Centered hero content */}
      <div className="flex flex-1 items-center justify-center px-4 py-12">
        <div className="flex w-full max-w-3xl flex-col items-center gap-8">
          {/* Top label */}
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full rounded-full bg-accent-success animate-pulse-dot" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-accent-success" />
            </span>
            <span className="font-mono text-xs uppercase tracking-widest text-text-accent">
              SEC Filing Risk Intelligence
            </span>
          </div>

          {/* Headline */}
          <h1 className="text-center text-4xl font-bold leading-tight text-text-primary sm:text-5xl">
            Identify what changed.
            <br />
            Understand what it means.
          </h1>

          {/* Subheadline */}
          <p className="max-w-2xl text-center text-base text-text-secondary sm:text-lg">
            Agentic analysis of 10-K Risk Factors and MD&amp;A across filing
            years — built for equity research analysts.
          </p>

          {/* Input card */}
          <div className="w-full max-w-2xl">
            <AnalysisForm />
          </div>

          {/* Feature pills */}
          <FeaturePills />
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-border-subtle px-4 py-3 text-center font-mono text-[11px] text-text-muted">
        Data sourced from SEC EDGAR · Not financial advice · For research use
        only
      </div>
    </div>
  );
}
