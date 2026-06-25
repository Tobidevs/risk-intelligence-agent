const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Company = {
  ticker: string;
  title: string;
  cik: string;
};

/**
 * Search the backend ticker directory (SEC-backed) by company name or ticker.
 * Pass an AbortSignal to cancel in-flight requests as the user keeps typing.
 */
export async function searchTickers(
  query: string,
  signal?: AbortSignal,
): Promise<Company[]> {
  const trimmed = query.trim();
  if (!trimmed) return [];

  const url = new URL("/tickers/search", API_BASE_URL);
  url.searchParams.set("q", trimmed);
  url.searchParams.set("limit", "20");

  const res = await fetch(url, { signal });
  if (!res.ok) {
    throw new Error(`Ticker search failed: ${res.status}`);
  }
  return (await res.json()) as Company[];
}
