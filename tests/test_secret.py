import os
import pytest
from httpx import AsyncClient
from app.main import app

# Set the secret for testing
os.environ["QUIZ_SECRET"] = "test-secret"


@pytest.mark.asyncio
async def test_rejects_wrong_secret():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/quiz", json={
            "secret": "wrong-secret",
            "url": "https://example.com"
        })
    assert resp.status_code == 403
    assert resp.json()["message"].lower().startswith("invalid")


@pytest.mark.asyncio
async def test_accepts_correct_secret():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/quiz", json={
            "secret": "test-secret",
            "url": "https://example.com"
        })
    # Because example.com returns HTML and solver may not find answer,
    # we only test: request is accepted, not solved.
    assert resp.status_code != 403
