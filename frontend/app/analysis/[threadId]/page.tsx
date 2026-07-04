"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import RiskFactorSelector from "@/components/RiskFactorSelector";
import {
  getAnalysis,
  submitSelection,
  type RiskFactor,
} from "@/lib/analysis";

export default function SelectionPage() {
  const router = useRouter();
  const params = useParams<{ threadId: string }>();
  const threadId = params.threadId;

  const [factors, setFactors] = useState<RiskFactor[] | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let active = true;
    getAnalysis(threadId)
      .then((data) => {
        if (active) setFactors(data.current_year_risk_factors);
      })
      .catch((err) => {
        if (active)
          setLoadError(
            err instanceof Error ? err.message : "Failed to load risk factors.",
          );
      });
    return () => {
      active = false;
    };
  }, [threadId]);

  const toggle = useCallback((id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const handleAssess = async () => {
    if (selectedIds.size === 0 || submitting) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const { assessment } = await submitSelection(
        threadId,
        Array.from(selectedIds),
      );
      // Hand the assessment to the results page (survives refresh within the tab).
      sessionStorage.setItem(
        `assessment:${threadId}`,
        JSON.stringify(assessment),
      );
      router.push(`/analysis/${threadId}/results`);
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : "Failed to assess risk factors.",
      );
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 py-12">
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full rounded-full bg-accent-primary animate-pulse-dot" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-accent-primary" />
          </span>
          <span className="font-mono text-xs uppercase tracking-widest text-text-accent">
            Step 2 — Select Risk Factors
          </span>
        </div>
        <h1 className="text-2xl font-bold text-text-primary sm:text-3xl">
          Choose the risk factors to assess
        </h1>
        <p className="text-sm text-text-secondary">
          The workflow gathered every risk factor from the filing. Select the
          ones worth a deeper look — only those continue to assessment.
        </p>
      </div>

        {loadError ? (
          <div className="rounded-sm border border-border-default bg-bg-surface p-6">
            <p className="font-mono text-sm text-accent-danger">{loadError}</p>
            <Link
              href="/"
              className="mt-3 inline-block font-mono text-xs uppercase tracking-widest text-text-accent hover:underline"
            >
              ← Start over
            </Link>
          </div>
        ) : factors === null ? (
          <div className="flex items-center gap-3 rounded-sm border border-border-default bg-bg-surface p-6">
            <span
              className="h-4 w-4 animate-spin rounded-full border-2 border-text-muted border-t-text-accent"
              aria-hidden="true"
            />
            <span className="font-mono text-sm text-text-secondary">
              Loading risk factors…
            </span>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between font-mono text-xs uppercase tracking-widest text-text-muted">
              <span>{factors.length} risk factors gathered</span>
              <span>{selectedIds.size} selected</span>
            </div>

            <RiskFactorSelector
              factors={factors}
              selectedIds={selectedIds}
              onToggle={toggle}
            />

            <div className="sticky bottom-0 flex flex-col gap-2 border-t border-border-subtle bg-bg-primary/95 py-4">
              <button
                type="button"
                onClick={handleAssess}
                disabled={selectedIds.size === 0 || submitting}
                className="flex w-full items-center justify-center gap-2 rounded-sm bg-accent-primary px-4 py-3.5 font-mono text-sm font-medium uppercase tracking-widest text-white transition-colors hover:bg-[#3b82f6] focus:outline-none focus:ring-2 focus:ring-accent-primary focus:ring-offset-2 focus:ring-offset-bg-primary disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-accent-primary"
              >
                {submitting ? (
                  <>
                    <span
                      className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"
                      aria-hidden="true"
                    />
                    Assessing {selectedIds.size} risk factor
                    {selectedIds.size === 1 ? "" : "s"}…
                  </>
                ) : (
                  `Assess ${selectedIds.size} selected →`
                )}
              </button>
              {submitError ? (
                <p className="text-center font-mono text-xs text-accent-danger">
                  {submitError}
                </p>
              ) : null}
            </div>
          </>
        )}
    </div>
  );
}
