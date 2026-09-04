# payment_processor.py — has multiple identical call patterns (for step-5 demo)
from legacy_orders import process_order


async def handle_payment_success(order_id: str) -> None:
    # called after payment confirmed
    await process_order(order_id, validate=True)


async def handle_payment_retry(order_id: str) -> None:
    # called on payment retry
    await process_order(order_id, validate=True)


async def handle_payment_failure(order_id: str) -> None:
    # called on payment failure — reprocess with legacy
    await process_order(order_id, validate=True)
