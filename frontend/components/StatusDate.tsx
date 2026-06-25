"use client";

import { useEffect, useState } from "react";

export default function StatusDate() {
  const [date, setDate] = useState("");

  useEffect(() => {
    const now = new Date();
    const formatted = now
      .toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "2-digit",
      })
      .toUpperCase();
    setDate(formatted);
  }, []);

  // Render an empty, fixed-width placeholder until mounted to avoid hydration mismatch.
  return <span className="tabular-nums">{date || " "}</span>;
}
