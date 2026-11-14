"""Validate ticker identifiers before they become local paths or upstream requests."""

import re

from fastapi import HTTPException


def normalize_symbol(symbol: str) -> str:
    value = symbol.strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{1,20}", value):
        raise HTTPException(400, "Mã chứng khoán không hợp lệ.")
    return value
