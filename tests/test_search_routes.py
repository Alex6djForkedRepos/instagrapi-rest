import pytest
from httpx import ASGITransport, AsyncClient

from aiograpi_rest.dependencies import get_clients
from aiograpi_rest.main import app


def _user_short(pk=1):
    return {"pk": str(pk), "username": f"user{pk}", "full_name": f"User {pk}"}


def _hashtag_payload(name="python"):
    return {"id": f"tag-{name}", "name": name, "media_count": 123}


def _location_payload(pk=1):
    return {"pk": pk, "name": "Berlin", "lat": 52.52, "lng": 13.405}


def _track_payload(track_id="track-1"):
    return {
        "id": track_id,
        "title": "Track",
        "subtitle": "Artist",
        "display_artist": "Artist",
        "audio_cluster_id": 1,
        "highlight_start_times_in_ms": [0],
        "is_explicit": False,
        "dash_manifest": "",
        "has_lyrics": False,
        "audio_asset_id": 10,
        "duration_in_ms": 30000,
        "allows_saving": True,
        "territory_validity_periods": {},
    }


class FakeSearchClient:
    def __init__(self):
        self.calls = []

    async def search_hashtags(self, query):
        self.calls.append(("search_hashtags", query))
        return [_hashtag_payload(query)]

    async def search_music(self, query):
        self.calls.append(("search_music", query))
        return [_track_payload()]

    async def fbsearch_places(self, query, lat=40.74, lng=-73.94):
        self.calls.append(("fbsearch_places", query, lat, lng))
        return [_location_payload()]

    async def web_search_topsearch(self, query):
        self.calls.append(("web_search_topsearch", query))
        return {"hashtags": [{"hashtag": _hashtag_payload(query)}], "users": [_user_short()]}

    async def web_search_topsearch_hashtags(self, query):
        self.calls.append(("web_search_topsearch_hashtags", query))
        return [_hashtag_payload(query)]

    async def fbsearch_topsearch_flat(self, query):
        self.calls.append(("fbsearch_topsearch_flat", query))
        return [{"type": "user", "user": _user_short()}]

    async def fbsearch_topsearch_v2(
        self,
        query,
        next_max_id=None,
        reels_max_id=None,
        rank_token=None,
    ):
        self.calls.append(("fbsearch_topsearch_v2", query, next_max_id, reels_max_id, rank_token))
        return {"items": [{"type": "user", "user": _user_short()}], "next_max_id": "next-top"}

    async def fbsearch_reels_v2(self, query, reels_max_id=None, rank_token=None):
        self.calls.append(("fbsearch_reels_v2", query, reels_max_id, rank_token))
        return {"items": [{"media": {"pk": 1}}], "reels_max_id": "next-reels"}

    async def fbsearch_accounts_v2(self, query, page_token=None):
        self.calls.append(("fbsearch_accounts_v2", query, page_token))
        return {"items": [_user_short()], "page_token": "next-accounts"}

    async def search_followers_v1(self, user_id, query):
        self.calls.append(("search_followers_v1", user_id, query))
        return [_user_short(2)]

    async def search_following_v1(self, user_id, query):
        self.calls.append(("search_following_v1", user_id, query))
        return [_user_short(3)]

    async def fbsearch_recent(self):
        self.calls.append(("fbsearch_recent",))
        return [(123, _user_short(4))]

    async def fbsearch_keyword_typeahead(self, query, timezone_offset=0, count=30):
        self.calls.append(("fbsearch_keyword_typeahead", query, timezone_offset, count))
        return {"items": [{"keyword": query}], "status": "ok"}

    async def fbsearch_typeahead_stream(self, query, timezone_offset=0, count=30):
        self.calls.append(("fbsearch_typeahead_stream", query, timezone_offset, count))
        return {"stream_rows": [{"users": [_user_short(5)]}], "status": "ok"}

    async def fbsearch_typehead(self, query):
        self.calls.append(("fbsearch_typehead", query))
        return [{"pk": "6", "username": "typeahead_user"}]

    async def fbsearch_item(
        self,
        item_id,
        search_surface,
        query,
        timezone_offset=0,
        count=30,
        reels_page_index=None,
        has_more_reels=None,
        reels_max_id=None,
        next_max_id=None,
        rank_token=None,
        page_index=None,
        page_token=None,
        paging_token=None,
    ):
        self.calls.append((
            "fbsearch_item",
            item_id,
            search_surface,
            query,
            timezone_offset,
            count,
            reels_page_index,
            has_more_reels,
            reels_max_id,
            next_max_id,
            rank_token,
            page_index,
            page_token,
            paging_token,
        ))
        return {"item_id": item_id, "query": query, "items": []}

    async def fbsearch_suggested_profiles(self, user_id):
        self.calls.append(("fbsearch_suggested_profiles", user_id))
        return [_user_short(7)]


class FakeStorage:
    def __init__(self):
        self.client = FakeSearchClient()

    async def get(self, sessionid):
        return self.client

    def close(self):
        pass


@pytest.fixture
def storage():
    fake = FakeStorage()
    app.dependency_overrides[get_clients] = lambda: fake
    yield fake
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_search_p0_routes_call_aiograpi_methods(storage):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        hashtags = await ac.get("/search/hashtags", params={"sessionid": "sid", "query": "python"})
        music = await ac.get("/search/music", params={"sessionid": "sid", "query": "rock"})
        places = await ac.get(
            "/search/places",
            params={"sessionid": "sid", "query": "Berlin", "lat": "52.52", "lng": "13.405"},
        )
        web_top = await ac.get("/search/web/top", params={"sessionid": "sid", "query": "python"})
        web_hashtags = await ac.get("/search/web/hashtags", params={"sessionid": "sid", "query": "python"})
        top_flat = await ac.get("/search/top/flat", params={"sessionid": "sid", "query": "python"})
        top = await ac.get(
            "/search/top",
            params={
                "sessionid": "sid",
                "query": "python",
                "next_max_id": "top-cursor",
                "reels_max_id": "reels-cursor",
                "rank_token": "rank",
            },
        )
        reels = await ac.get(
            "/search/reels",
            params={"sessionid": "sid", "query": "python", "reels_max_id": "reels-cursor", "rank_token": "rank"},
        )
        accounts = await ac.get(
            "/search/accounts",
            params={"sessionid": "sid", "query": "insta", "page_token": "accounts-cursor"},
        )
        followers = await ac.get(
            "/search/followers",
            params={"sessionid": "sid", "user_id": "1", "query": "alex"},
        )
        following = await ac.get(
            "/search/following",
            params={"sessionid": "sid", "user_id": "1", "query": "sam"},
        )
        recent = await ac.get("/search/recent", params={"sessionid": "sid"})
        typeahead = await ac.get(
            "/search/typeahead",
            params={"sessionid": "sid", "query": "py", "timezone_offset": "10800", "count": "5"},
        )
        typeahead_stream = await ac.get(
            "/search/typeahead/stream",
            params={"sessionid": "sid", "query": "py", "timezone_offset": "10800", "count": "5"},
        )
        typeahead_users = await ac.get(
            "/search/typeahead/users",
            params={"sessionid": "sid", "query": "py"},
        )
        item = await ac.get(
            "/search/item",
            params={
                "sessionid": "sid",
                "item_id": "clips_serp_page",
                "search_surface": "clips_serp_page",
                "query": "python",
                "timezone_offset": "10800",
                "count": "12",
                "reels_page_index": "2",
                "has_more_reels": "true",
                "reels_max_id": "reels-cursor",
                "next_max_id": "next-cursor",
                "rank_token": "rank",
                "page_index": "3",
                "page_token": "page",
                "paging_token": "paging",
            },
        )
        suggested = await ac.get(
            "/search/suggested/users",
            params={"sessionid": "sid", "user_id": "42"},
        )

    for response in (
        hashtags,
        music,
        places,
        web_top,
        web_hashtags,
        top_flat,
        top,
        reels,
        accounts,
        followers,
        following,
        recent,
        typeahead,
        typeahead_stream,
        typeahead_users,
        item,
        suggested,
    ):
        assert response.status_code == 200

    assert hashtags.json()[0]["name"] == "python"
    assert music.json()[0]["title"] == "Track"
    assert places.json()[0]["name"] == "Berlin"
    assert web_top.json()["hashtags"][0]["hashtag"]["name"] == "python"
    assert web_hashtags.json()[0]["name"] == "python"
    assert top_flat.json()[0]["type"] == "user"
    assert top.json()["next_max_id"] == "next-top"
    assert reels.json()["reels_max_id"] == "next-reels"
    assert accounts.json()["page_token"] == "next-accounts"
    assert followers.json()[0]["pk"] == "2"
    assert following.json()[0]["pk"] == "3"
    assert recent.json() == [{"timestamp": 123, "item": _user_short(4)}]
    assert typeahead.json()["items"][0]["keyword"] == "py"
    assert typeahead_stream.json()["stream_rows"][0]["users"][0]["pk"] == "5"
    assert typeahead_users.json()[0]["username"] == "typeahead_user"
    assert item.json()["item_id"] == "clips_serp_page"
    assert suggested.json()[0]["pk"] == "7"

    assert ("search_hashtags", "python") in storage.client.calls
    assert ("search_music", "rock") in storage.client.calls
    assert ("fbsearch_places", "Berlin", 52.52, 13.405) in storage.client.calls
    assert ("web_search_topsearch", "python") in storage.client.calls
    assert ("web_search_topsearch_hashtags", "python") in storage.client.calls
    assert ("fbsearch_topsearch_flat", "python") in storage.client.calls
    assert ("fbsearch_topsearch_v2", "python", "top-cursor", "reels-cursor", "rank") in storage.client.calls
    assert ("fbsearch_reels_v2", "python", "reels-cursor", "rank") in storage.client.calls
    assert ("fbsearch_accounts_v2", "insta", "accounts-cursor") in storage.client.calls
    assert ("search_followers_v1", "1", "alex") in storage.client.calls
    assert ("search_following_v1", "1", "sam") in storage.client.calls
    assert ("fbsearch_recent",) in storage.client.calls
    assert ("fbsearch_keyword_typeahead", "py", 10800, 5) in storage.client.calls
    assert ("fbsearch_typeahead_stream", "py", 10800, 5) in storage.client.calls
    assert ("fbsearch_typehead", "py") in storage.client.calls
    assert (
        "fbsearch_item",
        "clips_serp_page",
        "clips_serp_page",
        "python",
        10800,
        12,
        2,
        "true",
        "reels-cursor",
        "next-cursor",
        "rank",
        3,
        "page",
        "paging",
    ) in storage.client.calls
    assert ("fbsearch_suggested_profiles", "42") in storage.client.calls
