const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type RiskCategory =
  | "Market Risk"
  | "Credit Risk"
  | "Operational Risk"
  | "Regulatory/Compliance Risk"
  | "Strategic Risk"
  | "Reputational Risk";

/** A single risk factor gathered from Item 1A, tagged with a selection id. */
export type RiskFactor = {
  id: number;
  title: string;
  summary: string | null;
  category: RiskCategory | null;
  verbatim_text: string;
};

/** One assessed risk factor (stub output until real analysis lands). */
export type Assessment = {
  title: string;
  category: RiskCategory | null;
  status: string;
  note: string | null;
};

export type StartResponse = {
  thread_id: string;
  current_year_risk_factors: RiskFactor[];
};

export type SelectResponse = {
  thread_id: string;
  assessment: Assessment[];
};

async function parseError(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: unknown };
    if (typeof body?.detail === "string") return body.detail;
  } catch {
    // fall through to the status-based message
  }
  return `Request failed: ${res.status}`;
}

/**
 * Start a run. The workflow gathers every risk factor, then pauses; the
 * returned thread_id identifies the paused run for selection and resume.
 */
export async function startAnalysis(input: {
  cik: string;
  currentYear: number;
  priorYear: number;
}): Promise<StartResponse> {
  const res = await fetch(new URL("/analysis/start", API_BASE_URL), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      cik: input.cik,
      current_year: input.currentYear,
      prior_year: input.priorYear,
    }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as StartResponse;
}

/** Re-fetch a paused run's gathered risk factors (survives page refresh). */
export async function getAnalysis(threadId: string): Promise<StartResponse> {
  const res = await fetch(
    new URL(`/analysis/${encodeURIComponent(threadId)}`, API_BASE_URL),
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as StartResponse;
}

/** Resume a paused run with the chosen factor ids and return the assessment. */
export async function submitSelection(
  threadId: string,
  selectedIds: number[],
): Promise<SelectResponse> {
  const res = await fetch(
    new URL(`/analysis/${encodeURIComponent(threadId)}/select`, API_BASE_URL),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ selected_ids: selectedIds }),
    },
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as SelectResponse;
}
