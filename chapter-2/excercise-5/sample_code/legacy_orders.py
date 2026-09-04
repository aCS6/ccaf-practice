# legacy_orders.py — defines the deprecated and new functions


async def process_legacy_order(order_id: str) -> None:
    """Deprecated. Use process_order() instead."""
    print(f"Processing legacy order: {order_id}")


async def process_order(order_id: str, *, validate: bool = True) -> None:
    """New API — replaces process_legacy_order."""
    print(f"Processing order: {order_id}, validate: {validate}")
