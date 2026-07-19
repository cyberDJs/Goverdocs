from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from .utils import utc_now, write_json


def create_receipt(root: Path, command: str, result: str, **payload: Any) -> Path:
    receipt_id = f"RCPT-{uuid.uuid4().hex[:12].upper()}"
    target = root / "evidence/receipts" / f"{receipt_id}.json"
    write_json(target, {
        "receipt_id": receipt_id, "created_at": utc_now(), "command": command,
        "root": str(root.resolve()), "result": result, **payload,
    })
    return target
