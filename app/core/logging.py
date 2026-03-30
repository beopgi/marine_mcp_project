"""Logging utilities for the prototype service."""

import logging


def setup_logging(level: str = 'INFO') -> None:
    """Configure global logging format and level."""

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    )
