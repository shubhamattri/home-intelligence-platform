"""Worker process entrypoint: consumes the Redis job queue. Run in its own container."""

from __future__ import annotations

import asyncio

from jobs import make_store, run_worker

from .settings import settings
from .tasks import TASKS


def main() -> None:
    store = make_store(settings.redis_url)
    asyncio.run(run_worker(store, TASKS))


if __name__ == "__main__":
    main()
