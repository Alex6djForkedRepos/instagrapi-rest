from typing import Any, Dict, List, Optional

from aiograpi.types import Note
from fastapi import APIRouter, Depends, Form, Query
from pydantic import BaseModel

from aiograpi_rest.dependencies import ClientStorage, get_clients, get_sessionid

router = APIRouter(
    tags=["Note"],
    responses={404: {"description": "Not found"}},
)


class MusicNoteCreate(BaseModel):
    track: Dict[str, Any]
    text: str = ""
    audience: int = 0
    start_time: Optional[int] = None
    duration: int = 30000
    browse_session_id: Optional[str] = None
    alacorn_session_id: Optional[str] = None


@router.get("/notes", response_model=List[Note])
async def notes(
    sessionid: str = Depends(get_sessionid),
    clients: ClientStorage = Depends(get_clients),
) -> List[Note]:
    """List notes
    """
    cl = await clients.get(sessionid)
    return await cl.get_notes()


@router.get("/notes/music/browser", response_model=Dict[str, Any])
async def notes_music_browser(
    sessionid: str = Depends(get_sessionid),
    clients: ClientStorage = Depends(get_clients),
) -> Dict[str, Any]:
    """Browse note music
    """
    cl = await clients.get(sessionid)
    return await cl.notes_music_browser()


@router.patch("/notes/last-seen", response_model=bool)
async def notes_last_seen(
    sessionid: str = Depends(get_sessionid),
    clients: ClientStorage = Depends(get_clients),
) -> bool:
    """Mark notes as seen
    """
    cl = await clients.get(sessionid)
    return await cl.last_seen_update_note()


@router.get("/note", response_model=Optional[Note])
async def note_by_user(
    sessionid: str = Depends(get_sessionid),
    username: str = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> Optional[Note]:
    """Get note by username
    """
    cl = await clients.get(sessionid)
    notes_list = await cl.get_notes()
    return cl.get_note_by_user(notes_list, username.strip().lstrip("@"))


@router.get("/note/text", response_model=Optional[str])
async def note_text_by_user(
    sessionid: str = Depends(get_sessionid),
    username: str = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> Optional[str]:
    """Get note text by username
    """
    cl = await clients.get(sessionid)
    notes_list = await cl.get_notes()
    return cl.get_note_text_by_user(notes_list, username.strip().lstrip("@"))


@router.post("/note", response_model=Note)
async def note_create(
    sessionid: str = Depends(get_sessionid),
    text: str = Form(...),
    audience: int = Form(0),
    clients: ClientStorage = Depends(get_clients),
) -> Note:
    """Create a note
    """
    cl = await clients.get(sessionid)
    return await cl.create_note(text, audience)


@router.post("/note/music", response_model=Note)
async def note_music_create(
    payload: MusicNoteCreate,
    sessionid: str = Depends(get_sessionid),
    clients: ClientStorage = Depends(get_clients),
) -> Note:
    """Create a music note
    """
    cl = await clients.get(sessionid)
    return await cl.create_music_note(
        payload.track,
        text=payload.text,
        audience=payload.audience,
        start_time=payload.start_time,
        duration=payload.duration,
        browse_session_id=payload.browse_session_id,
        alacorn_session_id=payload.alacorn_session_id,
    )


@router.delete("/note", response_model=bool)
async def note_delete(
    sessionid: str = Depends(get_sessionid),
    note_id: int = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> bool:
    """Delete a note
    """
    cl = await clients.get(sessionid)
    return await cl.delete_note(note_id)
