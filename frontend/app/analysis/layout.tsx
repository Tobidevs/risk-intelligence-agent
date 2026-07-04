import type { ReactNode } from "react";
import Link from "next/link";
import StatusDate from "@/components/StatusDate";

/** Shared chrome for the analysis flow — mirrors the terminal frame on the home
 * hero (status bar, dot-grid backdrop, footer) so the selection and results
 * pages read as part of the same product. */
export default function AnalysisLayout({ children }: { children: ReactNode }) {
  return (
    <main className="relative min-h-screen bg-bg-primary">
      <div className="dot-grid pointer-events-none absolute inset-0" />

      <div className="relative z-10 flex min-h-screen flex-col">
        {/* Terminal status bar */}
        <div className="flex items-center justify-between border-b border-border-subtle px-4 py-2.5 font-mono text-[11px] uppercase tracking-widest text-text-muted">
          <Link href="/" className="transition-colors hover:text-text-secondary">
            FilingLens v0.1 Beta
          </Link>
          <StatusDate />
        </div>

        {/* Page content */}
        <div className="flex-1">{children}</div>

        {/* Footer */}
        <div className="border-t border-border-subtle px-4 py-3 text-center font-mono text-[11px] text-text-muted">
          Data sourced from SEC EDGAR · Not financial advice · For research use
          only
        </div>
      </div>
    </main>
  );
}
