from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any, Dict, List, Literal, Optional

from aiograpi.types import DirectMessage, DirectShortThread, DirectThread, Media, StoryMedia, StoryMention, UserShort
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from aiograpi_rest.dependencies import ClientStorage, get_clients, get_sessionid
from aiograpi_rest.helpers import parse_json_form_dict, parse_json_form_models
from aiograpi_rest.pagination import DirectThreadPage

router = APIRouter(
    prefix="/direct",
    tags=["Direct"],
    responses={404: {"description": "Not found"}},
)


class DirectMessageSearchResult(BaseModel):
    message: DirectMessage
    thread: DirectShortThread


STORY_MENTIONS_FORM_DESCRIPTION = (
    "Repeat this form field with a JSON-encoded StoryMention object, "
    "or pass one JSON array of StoryMention objects. Leave empty to omit."
)
STORY_MEDIAS_FORM_DESCRIPTION = (
    "Repeat this form field with a JSON-encoded StoryMedia object, "
    "or pass one JSON array of StoryMedia objects. Leave empty to omit."
)
EXTRA_DATA_FORM_DESCRIPTION = "JSON-encoded extra configure data. Leave empty to omit."


@router.get("/inbox", response_model=DirectThreadPage)
async def direct_inbox(
    sessionid: str = Depends(get_sessionid),
    selected_filter: Literal["", "flagged", "unread"] = Query(""),
    box: Literal["", "general", "primary"] = Query(""),
    thread_message_limit: Optional[int] = Query(None),
    cursor: str = Query(""),
    clients: ClientStorage = Depends(get_clients),
) -> DirectThreadPage:
    """Get a page of direct inbox threads
    """
    cl = await clients.get(sessionid)
    items, next_cursor = await cl.direct_threads_chunk(
        selected_filter,
        box,
        thread_message_limit,
        cursor or None,
    )
    return DirectThreadPage(items=items, next_cursor=next_cursor or "")


@router.get("/requests", response_model=List[DirectThread])
async def direct_requests(
    sessionid: str = Depends(get_sessionid),
    amount: int = Query(20),
    clients: ClientStorage = Depends(get_clients),
) -> List[DirectThread]:
    """List direct message requests
    """
    cl = await clients.get(sessionid)
    return await cl.direct_requests(amount)


@router.get("/pending/inbox", response_model=List[DirectThread])
async def direct_pending_inbox(
    sessionid: str = Depends(get_sessionid),
    amount: int = Query(20),
    clients: ClientStorage = Depends(get_clients),
) -> List[DirectThread]:
    """List direct pending inbox threads
    """
    cl = await clients.get(sessionid)
    return await cl.direct_pending_inbox(amount)


@router.get("/spam", response_model=DirectThreadPage)
async def direct_spam(
    sessionid: str = Depends(get_sessionid),
    cursor: str = Query(""),
    clients: ClientStorage = Depends(get_clients),
) -> DirectThreadPage:
    """Get a page of direct spam threads
    """
    cl = await clients.get(sessionid)
    items, next_cursor = await cl.direct_spam_chunk(cursor or None)
    return DirectThreadPage(items=items, next_cursor=next_cursor or "")


@router.get("/spam/inbox", response_model=List[DirectThread])
async def direct_spam_inbox(
    sessionid: str = Depends(get_sessionid),
    amount: int = Query(20),
    clients: ClientStorage = Depends(get_clients),
) -> List[DirectThread]:
    """List direct spam inbox threads
    """
    cl = await clients.get(sessionid)
    return await cl.direct_spam_inbox(amount)


@router.get("/threads", response_model=List[DirectThread])
async def direct_threads(
    sessionid: str = Depends(get_sessionid),
    amount: int = Query(20),
    selected_filter: Literal["", "flagged", "unread"] = Query(""),
    box: Literal["", "general", "primary"] = Query(""),
    thread_message_limit: Optional[int] = Query(None),
    clients: ClientStorage = Depends(get_clients),
) -> List[DirectThread]:
    """List direct threads
    """
    cl = await clients.get(sessionid)
    return await cl.direct_threads(amount, selected_filter, box, thread_message_limit)


@router.get("/thread", response_model=DirectThread)
async def direct_thread(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Query(...),
    amount: int = Query(20),
    clients: ClientStorage = Depends(get_clients),
) -> DirectThread:
    """Get direct thread details
    """
    cl = await clients.get(sessionid)
    return await cl.direct_thread(thread_id, amount)


@router.get("/thread/by/participants", response_model=Dict[str, Any])
async def direct_thread_by_participants(
    sessionid: str = Depends(get_sessionid),
    user_ids: List[int] = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> Dict[str, Any]:
    """Find a direct thread by participants
    """
    cl = await clients.get(sessionid)
    return await cl.direct_thread_by_participants(user_ids)


@router.patch("/thread", response_model=bool)
async def direct_thread_update(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Form(...),
    title: Optional[str] = Form(None),
    is_unread: Optional[bool] = Form(None),
    clients: ClientStorage = Depends(get_clients),
) -> bool:
    """Update direct thread state
    """
    if is_unread is False:
        raise HTTPException(status_code=422, detail="Only is_unread=true is supported")
    if title is None and is_unread is not True:
        raise HTTPException(status_code=422, detail="Provide title or is_unread=true")

    cl = await clients.get(sessionid)
    ok = True
    if title is not None:
        ok = ok and await cl.direct_thread_update_title(thread_id, title)
    if is_unread is True:
        ok = ok and await cl.direct_thread_mark_unread(thread_id)
    return ok


@router.delete("/thread", response_model=bool)
async def direct_thread_delete(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Query(...),
    move_to_spam: bool = Query(False),
    clients: ClientStorage = Depends(get_clients),
) -> bool:
    """Hide a direct thread
    """
    cl = await clients.get(sessionid)
    return await cl.direct_thread_hide(thread_id, move_to_spam)


@router.patch("/thread/seen", response_model=bool)
async def direct_thread_seen(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Form(...),
    clients: ClientStorage = Depends(get_clients),
) -> bool:
    """Mark a direct thread as seen
    """
    cl = await clients.get(sessionid)
    return await cl.direct_send_seen(thread_id)


@router.post("/thread/mute", response_model=bool)
async def direct_thread_mute(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Form(...),
    clients: ClientStorage = Depends(get_clients),
) -> bool:
    """Mute a direct thread
    """
    cl = await clients.get(sessionid)
    return await cl.direct_thread_mute(thread_id)


@router.delete("/thread/mute", response_model=bool)
async def direct_thread_unmute(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> bool:
    """Unmute a direct thread
    """
    cl = await clients.get(sessionid)
    return await cl.direct_thread_unmute(thread_id)


@router.post("/thread/video/call/mute", response_model=bool)
async def direct_thread_video_call_mute(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Form(...),
    clients: ClientStorage = Depends(get_clients),
) -> bool:
    """Mute direct thread video calls
    """
    cl = await clients.get(sessionid)
    return await cl.direct_thread_mute_video_call(thread_id)


@router.delete("/thread/video/call/mute", response_model=bool)
async def direct_thread_video_call_unmute(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> bool:
    """Unmute direct thread video calls
    """
    cl = await clients.get(sessionid)
    return await cl.direct_thread_unmute_video_call(thread_id)


@router.post("/thread/user", response_model=bool)
async def direct_thread_user_add(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Form(...),
    user_ids: List[int] = Form(...),
    clients: ClientStorage = Depends(get_clients),
) -> bool:
    """Add users to a direct thread
    """
    cl = await clients.get(sessionid)
    return await cl.direct_thread_add_users(thread_id, user_ids)


@router.get("/messages", response_model=List[DirectMessage])
async def direct_messages(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Query(...),
    amount: int = Query(20),
    clients: ClientStorage = Depends(get_clients),
) -> List[DirectMessage]:
    """List messages in a direct thread
    """
    cl = await clients.get(sessionid)
    return await cl.direct_messages(thread_id, amount)


@router.get("/messages/search", response_model=List[DirectMessageSearchResult])
async def direct_message_search(
    sessionid: str = Depends(get_sessionid),
    query: str = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> List[DirectMessageSearchResult]:
    """Search direct messages
    """
    cl = await clients.get(sessionid)
    return [
        DirectMessageSearchResult(message=message, thread=thread)
        for message, thread in await cl.direct_message_search(query)
    ]


@router.get("/message", response_model=DirectMessage)
async def direct_message(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Query(...),
    message_id: int = Query(...),
    amount: int = Query(20),
    clients: ClientStorage = Depends(get_clients),
) -> DirectMessage:
    """Get a direct message
    """
    cl = await clients.get(sessionid)
    return await cl.direct_message(thread_id, message_id, amount)


@router.post("/message/like", response_model=bool)
async def direct_message_like(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Form(...),
    message_id: int = Form(...),
    client_context: Optional[str] = Form(None),
    clients: ClientStorage = Depends(get_clients),
) -> bool:
    """Like a direct message
    """
    cl = await clients.get(sessionid)
    return await cl.direct_message_like(thread_id, message_id, client_context)


@router.delete("/message/like", response_model=bool)
async def direct_message_unlike(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Query(...),
    message_id: int = Query(...),
    client_context: Optional[str] = Query(None),
    clients: ClientStorage = Depends(get_clients),
) -> bool:
    """Unlike a direct message
    """
    cl = await clients.get(sessionid)
    return await cl.direct_message_unlike(thread_id, message_id, client_context)


@router.post("/message/reaction", response_model=bool)
async def direct_message_reaction_create(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Form(...),
    message_id: int = Form(...),
    emoji: str = Form("\u2764"),
    client_context: Optional[str] = Form(None),
    action_source: str = Form("double_tap"),
    target_item_type: Optional[str] = Form(None),
    clients: ClientStorage = Depends(get_clients),
) -> bool:
    """Create a direct message reaction
    """
    cl = await clients.get(sessionid)
    return await cl.direct_send_reaction(
        thread_id,
        message_id,
        emoji,
        client_context,
        action_source,
        target_item_type,
    )


@router.delete("/message/reaction", response_model=bool)
async def direct_message_reaction_delete(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Query(...),
    message_id: int = Query(...),
    emoji: str = Query("\u2764"),
    client_context: Optional[str] = Query(None),
    action_source: str = Query("double_tap"),
    target_item_type: Optional[str] = Query(None),
    clients: ClientStorage = Depends(get_clients),
) -> bool:
    """Delete a direct message reaction
    """
    cl = await clients.get(sessionid)
    return await cl.direct_delete_reaction(
        thread_id,
        message_id,
        emoji,
        client_context,
        action_source,
        target_item_type,
    )


@router.get("/pending", response_model=DirectThreadPage)
async def direct_pending(
    sessionid: str = Depends(get_sessionid),
    cursor: str = Query(""),
    clients: ClientStorage = Depends(get_clients),
) -> DirectThreadPage:
    """List pending direct thread requests
    """
    cl = await clients.get(sessionid)
    items, next_cursor = await cl.direct_pending_chunk(cursor or None)
    return DirectThreadPage(items=items, next_cursor=next_cursor or "")


@router.post("/request/approve", response_model=bool)
async def direct_request_approve(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Form(...),
    clients: ClientStorage = Depends(get_clients),
) -> bool:
    """Approve a direct message request
    """
    cl = await clients.get(sessionid)
    return await cl.direct_request_approve(thread_id)


@router.post("/thread/message", response_model=DirectMessage)
async def direct_thread_message(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Form(...),
    text: str = Form(...),
    clients: ClientStorage = Depends(get_clients),
) -> DirectMessage:
    """Reply in a direct thread
    """
    cl = await clients.get(sessionid)
    return await cl.direct_answer(thread_id, text)


@router.get("/search", response_model=List[UserShort])
async def direct_search(
    sessionid: str = Depends(get_sessionid),
    query: str = Query(...),
    mode: Literal["raven", "universal"] = Query("universal"),
    clients: ClientStorage = Depends(get_clients),
) -> List[UserShort]:
    """Search direct recipients
    """
    cl = await clients.get(sessionid)
    return await cl.direct_search(query, mode)


@router.get("/presence", response_model=Dict[str, Any])
async def direct_presence(
    sessionid: str = Depends(get_sessionid),
    user_ids: List[int] = Query([]),
    clients: ClientStorage = Depends(get_clients),
) -> Dict[str, Any]:
    """Get direct presence
    """
    cl = await clients.get(sessionid)
    if user_ids:
        return await cl.direct_users_presence(user_ids)
    return await cl.direct_active_presence()


@router.get("/media", response_model=List[Media])
async def direct_media(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Query(...),
    amount: int = Query(20),
    clients: ClientStorage = Depends(get_clients),
) -> List[Media]:
    """List direct thread media
    """
    cl = await clients.get(sessionid)
    return await cl.direct_media(thread_id, amount)


@router.post("/media", response_model=DirectMessage)
async def direct_media_share(
    sessionid: str = Depends(get_sessionid),
    media_id: str = Form(...),
    user_ids: List[int] = Form(...),
    send_attribute: str = Form("feed_timeline"),
    media_type: str = Form("photo"),
    clients: ClientStorage = Depends(get_clients),
) -> DirectMessage:
    """Share media to direct users
    """
    cl = await clients.get(sessionid)
    return await cl.direct_media_share(media_id, user_ids, send_attribute, media_type)


def _validate_direct_targets(user_ids: List[int], thread_ids: List[int]) -> None:
    if bool(user_ids) == bool(thread_ids):
        raise HTTPException(
            status_code=422,
            detail="Provide exactly one of user_ids or thread_ids",
        )


async def _write_direct_upload(file: UploadFile, directory: str, fallback_suffix: str) -> Path:
    suffix = Path(file.filename or "").suffix or fallback_suffix
    with NamedTemporaryFile(suffix=suffix, delete=False, dir=directory) as tmp:
        tmp.write(await file.read())
        return Path(tmp.name)


@router.post("/profile", response_model=DirectMessage)
async def direct_profile_share(
    sessionid: str = Depends(get_sessionid),
    user_id: str = Form(...),
    user_ids: List[int] = Form([]),
    thread_ids: List[int] = Form([]),
    clients: ClientStorage = Depends(get_clients),
) -> DirectMessage:
    """Share a profile to direct users or threads
    """
    _validate_direct_targets(user_ids, thread_ids)
    cl = await clients.get(sessionid)
    return await cl.direct_profile_share(user_id, user_ids, thread_ids)


@router.post("/story", response_model=DirectMessage)
async def direct_story_share(
    sessionid: str = Depends(get_sessionid),
    story_id: str = Form(...),
    user_ids: List[int] = Form([]),
    thread_ids: List[int] = Form([]),
    clients: ClientStorage = Depends(get_clients),
) -> DirectMessage:
    """Share a story to direct users or threads
    """
    _validate_direct_targets(user_ids, thread_ids)
    cl = await clients.get(sessionid)
    return await cl.direct_story_share(story_id, user_ids, thread_ids)


@router.post("/photo", response_model=DirectMessage)
async def direct_photo_send(
    sessionid: str = Depends(get_sessionid),
    file: UploadFile = File(...),
    user_ids: List[int] = Form([]),
    thread_ids: List[int] = Form([]),
    clients: ClientStorage = Depends(get_clients),
) -> DirectMessage:
    """Send a direct photo
    """
    _validate_direct_targets(user_ids, thread_ids)
    cl = await clients.get(sessionid)
    with TemporaryDirectory() as directory:
        path = await _write_direct_upload(file, directory, ".jpg")
        return await cl.direct_send_photo(path, user_ids, thread_ids)


@router.post("/video", response_model=DirectMessage)
async def direct_video_send(
    sessionid: str = Depends(get_sessionid),
    file: UploadFile = File(...),
    user_ids: List[int] = Form([]),
    thread_ids: List[int] = Form([]),
    clients: ClientStorage = Depends(get_clients),
) -> DirectMessage:
    """Send a direct video
    """
    _validate_direct_targets(user_ids, thread_ids)
    cl = await clients.get(sessionid)
    with TemporaryDirectory() as directory:
        path = await _write_direct_upload(file, directory, ".mp4")
        return await cl.direct_send_video(path, user_ids, thread_ids)


@router.post("/video/upload", response_model=DirectMessage)
async def direct_video_upload(
    sessionid: str = Depends(get_sessionid),
    file: UploadFile = File(...),
    caption: str = Form(""),
    thumbnail: Optional[UploadFile] = File(None),
    mentions: Optional[List[str]] = Form([], description=STORY_MENTIONS_FORM_DESCRIPTION),
    medias: Optional[List[str]] = Form([], description=STORY_MEDIAS_FORM_DESCRIPTION),
    thread_ids: List[int] = Form(...),
    extra_data: Optional[str] = Form(None, description=EXTRA_DATA_FORM_DESCRIPTION),
    clients: ClientStorage = Depends(get_clients),
) -> DirectMessage:
    """Upload a video to direct
    """
    cl = await clients.get(sessionid)
    parsed_mentions = parse_json_form_models(mentions, StoryMention, "mentions")
    parsed_medias = parse_json_form_models(medias, StoryMedia, "medias")
    parsed_extra_data = parse_json_form_dict(extra_data, "extra_data", default={})
    with TemporaryDirectory() as directory:
        path = await _write_direct_upload(file, directory, ".mp4")
        thumbnail_path = None
        if thumbnail is not None:
            thumbnail_path = await _write_direct_upload(thumbnail, directory, ".jpg")
        return await cl.video_upload_to_direct(
            path,
            caption=caption,
            thumbnail=thumbnail_path,
            mentions=parsed_mentions,
            medias=parsed_medias,
            thread_ids=thread_ids,
            extra_data=parsed_extra_data,
        )


@router.post("/voice", response_model=DirectMessage)
async def direct_voice_send(
    sessionid: str = Depends(get_sessionid),
    file: UploadFile = File(...),
    user_ids: List[int] = Form([]),
    thread_ids: List[int] = Form([]),
    waveform: Optional[List[float]] = Form(None),
    clients: ClientStorage = Depends(get_clients),
) -> DirectMessage:
    """Send a direct voice message
    """
    _validate_direct_targets(user_ids, thread_ids)
    cl = await clients.get(sessionid)
    with TemporaryDirectory() as directory:
        path = await _write_direct_upload(file, directory, ".m4a")
        return await cl.direct_send_voice(path, user_ids, thread_ids, waveform)


@router.post("/file", response_model=DirectMessage)
async def direct_file_send(
    sessionid: str = Depends(get_sessionid),
    file: UploadFile = File(...),
    user_ids: List[int] = Form([]),
    thread_ids: List[int] = Form([]),
    content_type: str = Form("photo"),
    clients: ClientStorage = Depends(get_clients),
) -> DirectMessage:
    """Send a direct file
    """
    _validate_direct_targets(user_ids, thread_ids)
    cl = await clients.get(sessionid)
    with TemporaryDirectory() as directory:
        path = await _write_direct_upload(file, directory, ".bin")
        return await cl.direct_send_file(path, user_ids, thread_ids, content_type)


@router.post("/cutout/sticker", response_model=DirectMessage)
async def direct_cutout_sticker_send(
    sessionid: str = Depends(get_sessionid),
    sticker_pk: str = Form(...),
    user_ids: List[int] = Form([]),
    thread_ids: List[int] = Form([]),
    clients: ClientStorage = Depends(get_clients),
) -> DirectMessage:
    """Send a direct cutout sticker
    """
    _validate_direct_targets(user_ids, thread_ids)
    cl = await clients.get(sessionid)
    return await cl.direct_send_cutout_sticker(sticker_pk, user_ids, thread_ids)


@router.post("/thread", response_model=str)
async def direct_thread_create(
    sessionid: str = Depends(get_sessionid),
    user_ids: List[int] = Form(...),
    title: str = Form(""),
    clients: ClientStorage = Depends(get_clients),
) -> str:
    """Create a direct thread
    """
    if len(user_ids) < 2:
        raise HTTPException(
            status_code=422,
            detail="Group threads require at least two recipient user_ids",
        )
    cl = await clients.get(sessionid)
    return await cl.direct_thread_create(user_ids, title)


@router.post("/message", response_model=DirectMessage)
async def direct_message_send(
    sessionid: str = Depends(get_sessionid),
    text: str = Form(...),
    user_ids: List[int] = Form([]),
    thread_ids: List[int] = Form([]),
    send_attribute: str = Form("message_button"),
    clients: ClientStorage = Depends(get_clients),
) -> DirectMessage:
    """Send a direct message
    """
    _validate_direct_targets(user_ids, thread_ids)
    cl = await clients.get(sessionid)
    return await cl.direct_send(text, user_ids, thread_ids, send_attribute)


@router.delete("/message", response_model=bool)
async def direct_message_delete(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Query(...),
    message_id: int = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> bool:
    """Unsend a direct message
    """
    cl = await clients.get(sessionid)
    return await cl.direct_message_unsend(thread_id, message_id)


@router.patch("/message/seen", response_model=bool)
async def direct_message_seen(
    sessionid: str = Depends(get_sessionid),
    thread_id: int = Form(...),
    message_id: int = Form(...),
    clients: ClientStorage = Depends(get_clients),
) -> bool:
    """Mark a direct message as seen
    """
    cl = await clients.get(sessionid)
    return await cl.direct_message_seen(thread_id, message_id)
