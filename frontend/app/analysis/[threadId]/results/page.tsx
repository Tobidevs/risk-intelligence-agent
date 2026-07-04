"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import type { Assessment } from "@/lib/analysis";

export default function ResultsPage() {
  const params = useParams<{ threadId: string }>();
  const threadId = params.threadId;
  const [assessment, setAssessment] = useState<Assessment[] | null>(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    const raw = sessionStorage.getItem(`assessment:${threadId}`);
    if (!raw) {
      setMissing(true);
      return;
    }
    try {
      setAssessment(JSON.parse(raw) as Assessment[]);
    } catch {
      setMissing(true);
    }
  }, [threadId]);

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 py-12">
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full rounded-full bg-accent-success animate-pulse-dot" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-accent-success" />
          </span>
          <span className="font-mono text-xs uppercase tracking-widest text-text-accent">
            Step 3 — Assessment
          </span>
        </div>
        <h1 className="text-2xl font-bold text-text-primary sm:text-3xl">
          Selected risk factor assessment
        </h1>
        <p className="text-sm text-text-secondary">
          In-depth assessment runs only on the factors you selected. Detailed
          analysis is coming soon — this is a preview of the assessed set.
        </p>
      </div>

        {missing ? (
          <div className="rounded-sm border border-border-default bg-bg-surface p-6">
            <p className="font-mono text-sm text-text-secondary">
              No assessment found for this run. It may have expired or the page
              was opened directly.
            </p>
            <Link
              href="/"
              className="mt-3 inline-block font-mono text-xs uppercase tracking-widest text-text-accent hover:underline"
            >
              ← Run a new analysis
            </Link>
          </div>
        ) : assessment === null ? (
          <p className="font-mono text-sm text-text-secondary">Loading…</p>
        ) : (
          <>
            <ul className="flex flex-col gap-3">
              {assessment.map((row, i) => (
                <li
                  key={i}
                  className="flex flex-col gap-1.5 rounded-sm border border-border-default bg-bg-surface p-4"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-semibold text-text-primary">
                      {row.title}
                    </span>
                    {row.category ? (
                      <span className="rounded-sm border border-border-default px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-text-secondary">
                        {row.category}
                      </span>
                    ) : null}
                    <span className="rounded-sm border border-accent-warning/40 bg-accent-warning/10 px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-accent-warning">
                      {row.status}
                    </span>
                  </div>
                  {row.note ? (
                    <p className="font-mono text-xs text-text-muted">{row.note}</p>
                  ) : null}
                </li>
              ))}
            </ul>

            <Link
              href="/"
              className="inline-block font-mono text-xs uppercase tracking-widest text-text-accent hover:underline"
            >
              ← Run another analysis
            </Link>
          </>
        )}
    </div>
  );
}
