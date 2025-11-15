import os
import json
import time
import traceback
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from pydantic import BaseModel
from playwright.sync_api import sync_playwright

from app.solver import solve_quiz
from dotenv import load_dotenv
load_dotenv()


# -------- ENVIRONMENT SECRET -------- #
QUIZ_SECRET = os.getenv("QUIZ_SECRET")
if not QUIZ_SECRET:
    raise RuntimeError("Environment variable QUIZ_SECRET not set.")


# -------- Pydantic Input Model -------- #
class QuizPayload(BaseModel):
    email: str
    secret: str
    url: str


app = FastAPI()


# -------- Utility: render JS page -------- #
def fetch_rendered_html(url: str) -> str:
    """
    Loads a webpage using Playwright (Chromium) and returns the final rendered HTML.
    Used because quizzes require JavaScript execution.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        html = page.content()
        browser.close()
        return html


# -------- Solve + Submit Loop -------- #
def solve_quiz_chain(email: str, secret: str, start_url: str):
    """
    Handles:
    - Fetching quiz page
    - Solving quiz
    - Submitting the answer
    - Following next quiz URLs if provided
    """

    current_url = start_url
    results = []

    deadline = time.time() + 180  # 3 minutes deadline

    while current_url:
        if time.time() > deadline:
            raise HTTPException(500, "Timeout: Quiz solving exceeded 3 minutes.")

        # STEP 1: Render quiz page
        html = fetch_rendered_html(current_url)

        # STEP 2: Solve quiz
        answer, submit_url = solve_quiz(html)

        if submit_url is None:
            raise HTTPException(500, "Quiz solver could not detect submit URL.")

        # STEP 3: Submit answer
        payload = {
            "email": email,
            "secret": secret,
            "url": current_url,
            "answer": answer,
        }

        try:
            submit_resp = requests.post(submit_url, json=payload, timeout=50)
            submit_json = submit_resp.json()
        except Exception:
            raise HTTPException(500, f"Submit failed for {current_url}")

        results.append({
            "quiz_url": current_url,
            "answer": answer,
            "submit_response": submit_json
        })

        # STEP 4: Continue if next URL provided
        if submit_json.get("correct") and submit_json.get("url"):
            current_url = submit_json["url"]
        elif not submit_json.get("correct") and submit_json.get("url"):
            # You may attempt retry or continue to next URL
            current_url = submit_json["url"]
        else:
            current_url = None

    return results


# -------- MAIN API ENDPOINT -------- #
@app.post("/")
async def solve(request: Request):
    """
    Main entry for quiz POST requests.
    Must return:
    - 400 on invalid JSON
    - 403 on wrong secret
    - 200 with solution steps on success
    """

    try:
        raw_body = await request.body()
        body_json = json.loads(raw_body.decode())
    except Exception:
        raise HTTPException(400, "Invalid JSON body.")

    try:
        data = QuizPayload(**body_json)
    except Exception:
        raise HTTPException(400, "Invalid payload format.")

    if data.secret != QUIZ_SECRET:
        raise HTTPException(403, "Invalid secret.")

    try:
        logs = solve_quiz_chain(
            email=data.email,
            secret=data.secret,
            start_url=data.url
        )
    except HTTPException as e:
        raise e
    except Exception:
        traceback.print_exc()
        raise HTTPException(500, "Internal server error while solving quiz.")

    return JSONResponse({"status": "ok", "steps": logs})
