from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/status")
def exports_status() -> dict[str, str]:
    return {"status": "planned"}

