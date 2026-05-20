import pytest
from httpx import ASGITransport, AsyncClient

from aiograpi_rest.dependencies import get_clients
from aiograpi_rest.main import app


class FakeShareClient:
    def __init__(self):
        self.calls = []

    def share_code_from_url(self, url):
        self.calls.append(("share_code_from_url", url))
        return "bWVkaWE6MTIz"

    def share_info_by_url(self, url):
        self.calls.append(("share_info_by_url", url))
        return {"type": "media", "pk": "123"}

    def share_info(self, code):
        self.calls.append(("share_info", code))
        return {"type": "highlight", "pk": "456"}


class FakeStorage:
    def __init__(self):
        self.client = FakeShareClient()

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
async def test_share_info_accepts_url_or_code(storage):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        by_url = await ac.get("/share", params={"sessionid": "sid", "url": "https://www.instagram.com/share/abc/"})
        by_code = await ac.get("/share", params={"sessionid": "sid", "code": "aGlnaGxpZ2h0OjQ1Ng=="})
        missing_selector = await ac.get("/share", params={"sessionid": "sid"})
        conflicting_selector = await ac.get(
            "/share",
            params={"sessionid": "sid", "url": "https://www.instagram.com/share/abc/", "code": "abc"},
        )

    assert by_url.status_code == 200
    assert by_url.json() == {"code": "bWVkaWE6MTIz", "pk": "123", "type": "media"}
    assert by_code.status_code == 200
    assert by_code.json() == {"code": "aGlnaGxpZ2h0OjQ1Ng==", "pk": "456", "type": "highlight"}
    assert missing_selector.status_code == 422
    assert conflicting_selector.status_code == 422
    assert ("share_code_from_url", "https://www.instagram.com/share/abc/") in storage.client.calls
    assert ("share_info_by_url", "https://www.instagram.com/share/abc/") in storage.client.calls
    assert ("share_info", "aGlnaGxpZ2h0OjQ1Ng==") in storage.client.calls
