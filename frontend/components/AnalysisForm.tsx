"use client";

import { useState } from "react";
import TickerInput from "./TickerInput";
import YearSelector from "./YearSelector";
import ScopeSelector from "./ScopeSelector";
import type { Company } from "../lib/tickers";

export default function AnalysisForm() {
  const [company, setCompany] = useState<Company | null>(null);
  const [baseYear, setBaseYear] = useState(2024);
  const [scopeMDA, setScopeMDA] = useState(true);
  const [scopeCrossRef, setScopeCrossRef] = useState(true);

  // Derived values
  const compareYear = baseYear - 1;

  const handleRun = () => {
    const config = {
      ticker: company?.ticker ?? null,
      resolvedCompany: company?.title ?? null,
      cik: company?.cik ?? null,
      baseYear,
      compareYear,
      scope: {
        riskFactors: true,
        mda: scopeMDA,
        crossReference: scopeCrossRef,
      },
    };
    // eslint-disable-next-line no-console
    console.log(config);
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
            disabled={!company}
            className="w-full rounded-sm bg-accent-primary px-4 py-3.5 font-mono text-sm font-medium uppercase tracking-widest text-white transition-colors hover:bg-[#3b82f6] focus:outline-none focus:ring-2 focus:ring-accent-primary focus:ring-offset-2 focus:ring-offset-bg-surface disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-accent-primary"
          >
            Run Analysis →
          </button>
          <p className="text-center font-mono text-xs text-text-muted">
            Analysis takes 45–90 seconds. Results include citations to source
            filings.
          </p>
        </div>
      </div>
    </div>
  );
}
