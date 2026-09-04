# test_refund_handler.py
import pytest
from refund_handler import reprocess_after_refund


@pytest.mark.asyncio
async def test_reprocess_after_refund():
    await reprocess_after_refund("ORD-001")
