# refund_handler.py — handles refund-related order reprocessing
from legacy_orders import process_order


async def reprocess_after_refund(order_id: str) -> None:
    await process_order(order_id, validate=True)
