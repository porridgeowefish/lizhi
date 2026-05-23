"""Compatibility wrapper for the DB-backed LLM queue worker."""
from __future__ import annotations

import asyncio

from llm_backfill import main


if __name__ == "__main__":
    asyncio.run(main())
