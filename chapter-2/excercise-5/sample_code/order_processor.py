# order_processor.py — processes incoming orders
from legacy_orders import process_order


async def handle_new_order(order_id: str) -> None:
    await process_order(order_id, validate=True)


async def handle_bulk_orders(order_ids: list[str]) -> None:
    for order_id in order_ids:
        await process_order(order_id, validate=True)
