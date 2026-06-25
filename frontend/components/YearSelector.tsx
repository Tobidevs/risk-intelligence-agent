"use client";

const BASE_YEAR_OPTIONS = [2024, 2023, 2022, 2021];

type YearSelectorProps = {
  baseYear: number;
  compareYear: number;
  onBaseYearChange: (year: number) => void;
};

export default function YearSelector({
  baseYear,
  compareYear,
  onBaseYearChange,
}: YearSelectorProps) {
  return (
    <div className="flex flex-col gap-2">
      <span className="font-mono text-xs uppercase tracking-widest text-text-muted">
        Analysis Period
      </span>

      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="base-year"
            className="font-mono text-[10px] uppercase tracking-widest text-text-muted"
          >
            Base Year
          </label>
          <select
            id="base-year"
            value={baseYear}
            onChange={(e) => onBaseYearChange(Number(e.target.value))}
            className="w-full cursor-pointer appearance-none rounded-sm border border-border-subtle bg-bg-elevated px-3 py-2.5 font-mono text-sm text-text-primary focus:border-accent-primary focus:outline-none focus:ring-1 focus:ring-accent-primary"
          >
            {BASE_YEAR_OPTIONS.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="compare-year"
            className="font-mono text-[10px] uppercase tracking-widest text-text-muted"
          >
            Compare Year
          </label>
          <select
            id="compare-year"
            value={compareYear}
            disabled
            aria-readonly="true"
            className="w-full cursor-not-allowed appearance-none rounded-sm border border-border-subtle bg-bg-elevated px-3 py-2.5 font-mono text-sm text-text-secondary opacity-70"
          >
            <option value={compareYear}>{compareYear}</option>
          </select>
        </div>
      </div>

      <p className="font-mono text-xs text-text-muted">
        FilingLens compares the two most recent 10-K filings by default.
      </p>
    </div>
  );
}
