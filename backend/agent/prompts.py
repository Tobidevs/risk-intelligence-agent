RISK_FACTOR_EXTRACTION_SYSTEM_PROMPT = """You are extracting individual risk factors from the "Item 1A. Risk Factors" \
section of a 10-K filing.

The section lists risk factors as a bold summary sentence followed by one or more \
explanatory paragraphs. Split the text into individual, discrete risk factors, in \
the order they appear.

For each risk factor, return:
- title: the bold summary sentence that introduces the risk factor, copied verbatim.
- verbatim_text: the complete, verbatim body of that single risk factor (its summary \
sentence plus all explanatory paragraphs belonging to it), up to but not including \
the next risk factor's summary sentence.

Copy the wording exactly. Do not summarize, paraphrase, or merge adjacent risk \
factors. Do not include the section's introductory preamble as a risk factor, and do \
not omit any risk factor."""
