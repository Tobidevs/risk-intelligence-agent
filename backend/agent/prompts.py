RISK_FACTOR_EXTRACTION_SYSTEM_PROMPT = """You are extracting individual risk factors from the "Item 1A. Risk Factors" \
section of a 10-K filing.

The section lists risk factors as a bold summary sentence followed by one or more \
explanatory paragraphs. Split the text into individual, discrete risk factors, in \
the order they appear.

For each risk factor, return:
- title: a concise, client-facing title (roughly 3-8 words) that you write to name \
the risk factor. Word it in clear, plain language that a client assessing this risk \
can understand at a glance. This is your own heading, NOT the verbatim summary \
sentence. For example, a factor whose summary sentence reads "The Company's future \
performance depends in part on support from third-party developers." might be titled \
"Reliance on Third-Party Developers".
- summary: a concise, client-facing summary (roughly 2-4 sentences) that you compose \
in plain language for a client assessing this risk. Explain what the risk is and why \
it matters to the company in accessible terms. Do NOT quote the filing verbatim — \
paraphrase and clarify.
- category: the single category that best classifies the risk factor, chosen from \
this exact set:
  - "Market Risk"
  - "Credit Risk"
  - "Operational Risk"
  - "Regulatory/Compliance Risk"
  - "Strategic Risk"
  - "Reputational Risk"
- verbatim_text: the complete, verbatim body of that single risk factor (its summary \
sentence plus all explanatory paragraphs belonging to it), up to but not including \
the next risk factor's summary sentence.

Copy the verbatim_text wording exactly. Do not summarize, paraphrase, or merge \
adjacent risk factors. Do not include the section's introductory preamble as a risk \
factor, and do not omit any risk factor."""
