"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import TickerInput from "./TickerInput";
import YearSelector from "./YearSelector";
import ScopeSelector from "./ScopeSelector";
import type { Company } from "../lib/tickers";
import { startAnalysis } from "../lib/analysis";

export default function AnalysisForm() {
  const router = useRouter();
  const [company, setCompany] = useState<Company | null>(null);
  const [baseYear, setBaseYear] = useState(2024);
  const [scopeMDA, setScopeMDA] = useState(true);
  const [scopeCrossRef, setScopeCrossRef] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Derived values
  const compareYear = baseYear - 1;

  const handleRun = async () => {
    if (!company || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      // The workflow gathers all risk factors, then pauses; navigate to the
      // selection page for this run, keyed by its thread_id.
      const { thread_id } = await startAnalysis({
        cik: company.cik,
        currentYear: baseYear,
        priorYear: compareYear,
      });
      router.push(`/analysis/${thread_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start analysis.");
      setSubmitting(false);
    }
  };

  return (
    <div className="w-full rounded-none border border-border-default bg-bg-surface p-6 sm:p-8">
      <div className="flex flex-col gap-6">
        <TickerInput selected={company} onSelect={setCompany} />

        <YearSelector
          baseYear={baseYear}
          compareYear={compareYear}
          onBaseYearChange={setBaseYear}
        />

        <ScopeSelector
          scopeMDA={scopeMDA}
          scopeCrossRef={scopeCrossRef}
          onToggleMDA={() => setScopeMDA((v) => !v)}
          onToggleCrossRef={() => setScopeCrossRef((v) => !v)}
        />

        <div className="flex flex-col gap-2">
          <button
            type="button"
            onClick={handleRun}
            disabled={!company || submitting}
            className="flex w-full items-center justify-center gap-2 rounded-sm bg-accent-primary px-4 py-3.5 font-mono text-sm font-medium uppercase tracking-widest text-white transition-colors hover:bg-[#3b82f6] focus:outline-none focus:ring-2 focus:ring-accent-primary focus:ring-offset-2 focus:ring-offset-bg-surface disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-accent-primary"
          >
            {submitting ? (
              <>
                <span
                  className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"
                  aria-hidden="true"
                />
                Gathering risk factors…
              </>
            ) : (
              "Run Analysis →"
            )}
          </button>
          {error ? (
            <p className="text-center font-mono text-xs text-accent-danger">
              {error}
            </p>
          ) : (
            <p className="text-center font-mono text-xs text-text-muted">
              Analysis takes 45–90 seconds. Results include citations to source
              filings.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
