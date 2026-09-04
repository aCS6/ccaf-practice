# test_order_processor.py
import pytest
from order_processor import handle_new_order, handle_bulk_orders


@pytest.mark.asyncio
async def test_handle_new_order():
    await handle_new_order("ORD-001")


@pytest.mark.asyncio
async def test_handle_bulk_orders():
    await handle_bulk_orders(["ORD-001", "ORD-002"])
