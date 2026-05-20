from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder

from aiograpi_rest.dependencies import ClientStorage, get_clients, get_sessionid

router = APIRouter(
    prefix="/share",
    tags=["Share"],
    responses={404: {"description": "Not found"}},
)


def _ensure_single_share_selector(url: Optional[str], code: Optional[str]) -> None:
    if not url and not code:
        raise HTTPException(status_code=422, detail="Provide url or code")
    if url and code:
        raise HTTPException(status_code=422, detail="Provide only one of url or code")


@router.get("", response_model=Dict[str, Any])
async def share_info(
    sessionid: str = Depends(get_sessionid),
    url: Optional[str] = Query(None),
    code: Optional[str] = Query(None),
    clients: ClientStorage = Depends(get_clients),
) -> Dict[str, Any]:
    """Get share info
    """
    _ensure_single_share_selector(url, code)
    cl = await clients.get(sessionid)
    if url:
        resolved_code = cl.share_code_from_url(url)
        share = cl.share_info_by_url(url)
    else:
        resolved_code = code
        share = cl.share_info(code)
    data = jsonable_encoder(share)
    return {"code": resolved_code, **data}
