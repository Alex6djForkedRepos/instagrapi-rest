import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Optional

from aiograpi.types import Highlight
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from aiograpi_rest.dependencies import ClientStorage, get_clients, get_sessionid

router = APIRouter(
    prefix="/highlight",
    tags=["Highlight"],
    responses={404: {"description": "Not found"}},
)


def _ensure_single_highlight_selector(highlight_pk: Optional[str], url: Optional[str]) -> None:
    if not highlight_pk and not url:
        raise HTTPException(status_code=422, detail="Provide highlight_pk or url")
    if highlight_pk and url:
        raise HTTPException(status_code=422, detail="Provide only one of highlight_pk or url")


async def _highlight_pk_from_selector(cl, highlight_pk: Optional[str], url: Optional[str]) -> str:
    _ensure_single_highlight_selector(highlight_pk, url)
    if url:
        return str(await cl.highlight_pk_from_url(url))
    return str(highlight_pk)


async def _change_highlight_cover(cl, highlight_pk: str, cover_picture: UploadFile) -> Highlight:
    suffix = Path(cover_picture.filename or "").suffix or ".jpg"
    tmp_path = None
    try:
        with NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(await cover_picture.read())
            tmp_path = Path(tmp.name)
        return await cl.highlight_change_cover(highlight_pk, tmp_path)
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


@router.get("", response_model=Highlight)
async def highlight(
    sessionid: str = Depends(get_sessionid),
    highlight_pk: Optional[str] = Query(None),
    url: Optional[str] = Query(None),
    clients: ClientStorage = Depends(get_clients),
) -> Highlight:
    """Get highlight info
    """
    cl = await clients.get(sessionid)
    highlight_pk = await _highlight_pk_from_selector(cl, highlight_pk, url)
    return await cl.highlight_info(highlight_pk)


@router.post("", response_model=Highlight)
async def highlight_create(
    sessionid: str = Depends(get_sessionid),
    title: str = Form(...),
    story_ids: List[str] = Form(...),
    cover_story_id: str = Form(""),
    crop_rect: List[float] = Form([0.0, 0.21830457, 1.0, 0.78094524]),
    clients: ClientStorage = Depends(get_clients),
) -> Highlight:
    """Create a highlight
    """
    cl = await clients.get(sessionid)
    return await cl.highlight_create(title, story_ids, cover_story_id, crop_rect)


@router.patch("", response_model=Highlight)
async def highlight_edit(
    sessionid: str = Depends(get_sessionid),
    highlight_pk: str = Form(...),
    title: str = Form(""),
    cover: Optional[str] = Form(None),
    cover_picture: Optional[UploadFile] = File(None),
    added_media_ids: List[str] = Form([]),
    removed_media_ids: List[str] = Form([]),
    clients: ClientStorage = Depends(get_clients),
) -> Highlight:
    """Update a highlight
    """
    if cover:
        try:
            cover_data = json.loads(cover)
        except json.JSONDecodeError:
            raise HTTPException(status_code=422, detail="cover must be valid JSON")
    else:
        cover_data = {}
    cl = await clients.get(sessionid)
    has_story_changes = bool(added_media_ids or removed_media_ids)
    if cover_picture and cover_data:
        raise HTTPException(status_code=422, detail="Provide only one of cover or cover_picture")
    if title and not cover_picture and not cover_data and not has_story_changes:
        return await cl.highlight_change_title(highlight_pk, title)
    if cover_picture and not title and not has_story_changes:
        return await _change_highlight_cover(cl, highlight_pk, cover_picture)
    if cover_picture:
        await cl.highlight_edit(
            highlight_pk,
            title,
            cover_data,
            added_media_ids,
            removed_media_ids,
        )
        return await _change_highlight_cover(cl, highlight_pk, cover_picture)
    return await cl.highlight_edit(
        highlight_pk,
        title,
        cover_data,
        added_media_ids,
        removed_media_ids,
    )


@router.delete("", response_model=bool)
async def highlight_delete(
    sessionid: str = Depends(get_sessionid),
    highlight_pk: str = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> bool:
    """Delete a highlight
    """
    cl = await clients.get(sessionid)
    return await cl.highlight_delete(highlight_pk)


@router.post("/story", response_model=Highlight)
async def highlight_story_add(
    sessionid: str = Depends(get_sessionid),
    highlight_pk: str = Form(...),
    story_ids: List[str] = Form(...),
    clients: ClientStorage = Depends(get_clients),
) -> Highlight:
    """Add stories to a highlight
    """
    cl = await clients.get(sessionid)
    return await cl.highlight_add_stories(highlight_pk, story_ids)


@router.delete("/story", response_model=Highlight)
async def highlight_story_remove(
    sessionid: str = Depends(get_sessionid),
    highlight_pk: str = Query(...),
    story_ids: List[str] = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> Highlight:
    """Remove stories from a highlight
    """
    cl = await clients.get(sessionid)
    return await cl.highlight_remove_stories(highlight_pk, story_ids)
