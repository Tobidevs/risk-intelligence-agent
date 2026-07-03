"""Braintrust tracing setup, shared by the FastAPI app and standalone scripts.

Ideally this runs before any AI library imports or client creation, per
https://www.braintrust.dev/docs/tracing-quickstart. In practice the
integrations this project relies on (LangChain, OpenAI) resolve their patch
targets dynamically at call time rather than at import time, so calling this
after those imports also works -- but call it as early as possible regardless.
"""

import braintrust

from app.core.config import get_settings

_PROJECT_NAME = "Risk-Intelligence-Agent"


def init_tracing() -> None:
    """Initialize Braintrust logging and auto-instrumentation.

    Safe to call more than once within a process: braintrust.auto_instrument()
    skips libraries it has already patched.
    """
    braintrust.init_logger(
        project=_PROJECT_NAME, api_key=get_settings().braintrust_api_key
    )
    braintrust.auto_instrument()
