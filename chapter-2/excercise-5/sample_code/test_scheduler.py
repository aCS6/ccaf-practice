# test_scheduler.py
import pytest
from scheduler import nightly_reprocess


@pytest.mark.asyncio
async def test_nightly_reprocess():
    await nightly_reprocess(["ORD-001", "ORD-002", "ORD-003"])
