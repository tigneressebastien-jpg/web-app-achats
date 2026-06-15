from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(prefix="/imports", tags=["imports"])


@router.get("/status")
def imports_status() -> dict[str, str]:
    return {"status": "planned"}

