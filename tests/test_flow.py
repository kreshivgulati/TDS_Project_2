import os
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from app.main import app

os.environ["QUIZ_SECRET"] = "test-secret"


@pytest.mark.asyncio
@patch("app.solver.solve_quiz")
@patch("app.browser.fetch_page_html")
async def test_full_quiz_flow(mock_fetch_html, mock_solver):
    """
    Simulates a complete quiz flow:

    1) POST /quiz with correct secret
    2) Mock fetching quiz HTML
    3) Mock solving quiz
    4) Mock submitting answer
    5) Flow continues until no new URL
    """

    # --- Mock HTML returned by browser ---
    mock_fetch_html.return_value = """
        <div id='result'>Test Quiz</div>
        <script>console.log("dummy")</script>
    """

    # --- Mock solver output ---
    # First quiz returns correct answer and new URL
    # Second quiz returns correct answer and ends
    mock_solver.side_effect = [
        {
            "answer": 111,
            "submit_url": "https://example.com/submit1",
            "next_url": "https://example.com/quiz-2"
        },
        {
            "answer": 222,
            "submit_url": "https://example.com/submit2",
            "next_url": None
        }
    ]

    # --- Mock HTTP POSTs to submission URLs ---
    async def mock_post(url, json):
        return AsyncMock(status_code=200, json=lambda: {"correct": True})

    with patch("httpx.AsyncClient.post", new=mock_post):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/quiz", json={
                "email": "test@example.com",
                "secret": "test-secret",
                "url": "https://example.com/quiz-1"
            })

    # Ensure initial request accepted
    assert response.status_code == 200

    # Solver should be called twice (2 quizzes)
    assert mock_solver.call_count == 2

    # Browser should fetch both pages
    assert mock_fetch_html.call_count == 2
