# scheduler.py — scheduled nightly reprocessing job
from utils import process_legacy_order  # imported via barrel module


async def nightly_reprocess(order_ids: list[str]) -> None:
    for order_id in order_ids:
        await process_legacy_order(order_id)
