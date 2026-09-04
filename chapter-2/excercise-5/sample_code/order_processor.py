# order_processor.py — processes incoming orders
from legacy_orders import process_legacy_order


async def handle_new_order(order_id: str) -> None:
    await process_legacy_order(order_id)


async def handle_bulk_orders(order_ids: list[str]) -> None:
    for order_id in order_ids:
        await process_legacy_order(order_id)
