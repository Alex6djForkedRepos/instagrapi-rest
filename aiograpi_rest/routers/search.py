from typing import Any, Dict, List, Optional

from aiograpi.types import Hashtag, Location, Track, UserShort
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from aiograpi_rest.dependencies import ClientStorage, get_clients, get_sessionid

router = APIRouter(
    prefix="/search",
    tags=["Search"],
    responses={404: {"description": "Not found"}},
)


class RecentSearchItem(BaseModel):
    timestamp: Optional[int] = None
    item: Any


@router.get("/users", response_model=List[UserShort])
async def search_users(
    sessionid: str = Depends(get_sessionid),
    query: str = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> List[UserShort]:
    """Search users
    """
    cl = await clients.get(sessionid)
    return await cl.search_users(query)


@router.get("/hashtags", response_model=List[Hashtag])
async def search_hashtags(
    sessionid: str = Depends(get_sessionid),
    query: str = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> List[Hashtag]:
    """Search hashtags
    """
    cl = await clients.get(sessionid)
    return await cl.search_hashtags(query)


@router.get("/music", response_model=List[Track])
async def search_music(
    sessionid: str = Depends(get_sessionid),
    query: str = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> List[Track]:
    """Search music tracks
    """
    cl = await clients.get(sessionid)
    return await cl.search_music(query)


@router.get("/locations", response_model=List[Location])
async def search_locations(
    sessionid: str = Depends(get_sessionid),
    name: Optional[str] = Query(None),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    clients: ClientStorage = Depends(get_clients),
) -> List[Location]:
    """Search locations by name or coordinates
    """
    cl = await clients.get(sessionid)
    if name:
        return await cl.location_search_name(name)
    if lat is None or lng is None:
        raise HTTPException(status_code=422, detail="Provide name or both lat and lng")
    return await cl.location_search(lat, lng)


@router.get("/places", response_model=List[Location])
async def search_places(
    sessionid: str = Depends(get_sessionid),
    query: str = Query(...),
    lat: float = Query(40.74),
    lng: float = Query(-73.94),
    clients: ClientStorage = Depends(get_clients),
) -> List[Location]:
    """Search places
    """
    cl = await clients.get(sessionid)
    return await cl.fbsearch_places(query, lat, lng)


@router.get("/web/top", response_model=Dict[str, Any])
async def search_web_top(
    sessionid: str = Depends(get_sessionid),
    query: str = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> Dict[str, Any]:
    """Search web top results
    """
    cl = await clients.get(sessionid)
    return await cl.web_search_topsearch(query)


@router.get("/web/hashtags", response_model=List[Hashtag])
async def search_web_hashtags(
    sessionid: str = Depends(get_sessionid),
    query: str = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> List[Hashtag]:
    """Search web hashtags
    """
    cl = await clients.get(sessionid)
    return await cl.web_search_topsearch_hashtags(query)


@router.get("/top", response_model=Dict[str, Any])
async def search_top(
    sessionid: str = Depends(get_sessionid),
    query: str = Query(...),
    next_max_id: Optional[str] = Query(None),
    reels_max_id: Optional[str] = Query(None),
    rank_token: Optional[str] = Query(None),
    clients: ClientStorage = Depends(get_clients),
) -> Dict[str, Any]:
    """Search top results
    """
    cl = await clients.get(sessionid)
    return await cl.fbsearch_topsearch_v2(
        query,
        next_max_id=next_max_id,
        reels_max_id=reels_max_id,
        rank_token=rank_token,
    )


@router.get("/top/flat", response_model=List[Dict[str, Any]])
async def search_top_flat(
    sessionid: str = Depends(get_sessionid),
    query: str = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> List[Dict[str, Any]]:
    """Search flat top results
    """
    cl = await clients.get(sessionid)
    return await cl.fbsearch_topsearch_flat(query)


@router.get("/reels", response_model=Dict[str, Any])
async def search_reels(
    sessionid: str = Depends(get_sessionid),
    query: str = Query(...),
    reels_max_id: Optional[str] = Query(None),
    rank_token: Optional[str] = Query(None),
    clients: ClientStorage = Depends(get_clients),
) -> Dict[str, Any]:
    """Search Reels
    """
    cl = await clients.get(sessionid)
    return await cl.fbsearch_reels_v2(query, reels_max_id=reels_max_id, rank_token=rank_token)


@router.get("/accounts", response_model=Dict[str, Any])
async def search_accounts(
    sessionid: str = Depends(get_sessionid),
    query: str = Query(...),
    page_token: Optional[str] = Query(None),
    clients: ClientStorage = Depends(get_clients),
) -> Dict[str, Any]:
    """Search accounts
    """
    cl = await clients.get(sessionid)
    return await cl.fbsearch_accounts_v2(query, page_token=page_token)


@router.get("/suggested/users", response_model=List[UserShort])
async def search_suggested_users(
    sessionid: str = Depends(get_sessionid),
    user_id: str = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> List[UserShort]:
    """List suggested users for a profile
    """
    cl = await clients.get(sessionid)
    return await cl.fbsearch_suggested_profiles(user_id)


@router.get("/followers", response_model=List[UserShort])
async def search_followers(
    sessionid: str = Depends(get_sessionid),
    user_id: str = Query(...),
    query: str = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> List[UserShort]:
    """Search a user's followers
    """
    cl = await clients.get(sessionid)
    return await cl.search_followers_v1(user_id, query)


@router.get("/following", response_model=List[UserShort])
async def search_following(
    sessionid: str = Depends(get_sessionid),
    user_id: str = Query(...),
    query: str = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> List[UserShort]:
    """Search accounts a user follows
    """
    cl = await clients.get(sessionid)
    return await cl.search_following_v1(user_id, query)


@router.get("/recent", response_model=List[RecentSearchItem])
async def search_recent(
    sessionid: str = Depends(get_sessionid),
    clients: ClientStorage = Depends(get_clients),
) -> List[RecentSearchItem]:
    """List recent searches
    """
    cl = await clients.get(sessionid)
    return [
        RecentSearchItem(timestamp=timestamp, item=item)
        for timestamp, item in await cl.fbsearch_recent()
    ]


@router.get("/typeahead", response_model=Dict[str, Any])
async def search_typeahead(
    sessionid: str = Depends(get_sessionid),
    query: str = Query(...),
    timezone_offset: int = Query(0),
    count: int = Query(30, ge=1, le=100),
    clients: ClientStorage = Depends(get_clients),
) -> Dict[str, Any]:
    """Get search autocomplete suggestions
    """
    cl = await clients.get(sessionid)
    return await cl.fbsearch_keyword_typeahead(query, timezone_offset=timezone_offset, count=count)


@router.get("/typeahead/stream", response_model=Dict[str, Any])
async def search_typeahead_stream(
    sessionid: str = Depends(get_sessionid),
    query: str = Query(...),
    timezone_offset: int = Query(0),
    count: int = Query(30, ge=1, le=100),
    clients: ClientStorage = Depends(get_clients),
) -> Dict[str, Any]:
    """Get raw search typeahead stream
    """
    cl = await clients.get(sessionid)
    return await cl.fbsearch_typeahead_stream(query, timezone_offset=timezone_offset, count=count)


@router.get("/typeahead/users", response_model=List[Dict[str, Any]])
async def search_typeahead_users(
    sessionid: str = Depends(get_sessionid),
    query: str = Query(...),
    clients: ClientStorage = Depends(get_clients),
) -> List[Dict[str, Any]]:
    """Get typeahead user suggestions
    """
    cl = await clients.get(sessionid)
    return await cl.fbsearch_typehead(query)


@router.get("/item", response_model=Dict[str, Any])
async def search_item(
    sessionid: str = Depends(get_sessionid),
    item_id: str = Query(...),
    search_surface: str = Query(...),
    query: str = Query(...),
    timezone_offset: int = Query(0),
    count: int = Query(30, ge=1, le=100),
    reels_page_index: Optional[int] = Query(None),
    has_more_reels: Optional[str] = Query(None),
    reels_max_id: Optional[str] = Query(None),
    next_max_id: Optional[str] = Query(None),
    rank_token: Optional[str] = Query(None),
    page_index: Optional[int] = Query(None),
    page_token: Optional[str] = Query(None),
    paging_token: Optional[str] = Query(None),
    clients: ClientStorage = Depends(get_clients),
) -> Dict[str, Any]:
    """Search one Instagram result tab
    """
    cl = await clients.get(sessionid)
    return await cl.fbsearch_item(
        item_id,
        search_surface,
        query,
        timezone_offset=timezone_offset,
        count=count,
        reels_page_index=reels_page_index,
        has_more_reels=has_more_reels,
        reels_max_id=reels_max_id,
        next_max_id=next_max_id,
        rank_token=rank_token,
        page_index=page_index,
        page_token=page_token,
        paging_token=paging_token,
    )
