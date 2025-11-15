# app/solver.py

import re
import base64
import pandas as pd
import requests
from bs4 import BeautifulSoup
from app.browser import Browser


def solve_quiz(html: str):
    """
    Main entry used by main.py:
        answer, submit_url = solve_quiz(html)

    Performs:
    - Parsing JS-rendered HTML
    - Extract quiz question
    - Identify submission URL
    - Load/download data if required
    - Compute final answer
    """

    soup = BeautifulSoup(html, "html.parser")

    # ------------------------------------------------------------
    # 1. Detect SUBMIT URL (always present in quiz instructions)
    # ------------------------------------------------------------
    submit_url = None
    code_blocks = soup.find_all("pre")

    for block in code_blocks:
        try:
            text = block.get_text().strip()
            data = eval(text) if text.startswith("{") else None
            if data and "email" in data and "secret" in data and "url" in data:
                # instructions tell: post answer to <submit_url>
                # The JSON payload in preview contains the correct submit URL
                # so fetch from the element above
                parent_text = block.find_previous(text=True)
                if "http" in parent_text:
                    # extract first URL
                    m = re.search(r"https?://[^\s\"]+", parent_text)
                    if m:
                        submit_url = m.group(0)
        except Exception:
            pass

    if not submit_url:
        # fallback: scan page for URLs
        matched = re.findall(r"https?://[^\s\"']+", html)
        if matched:
            submit_url = matched[-1]  # last is usually submit URL

    # ------------------------------------------------------------
    # 2. Extract QUESTION
    #    Usually text like: "Q123. Download file. What is the sum..."
    # ------------------------------------------------------------
    question_text = ""
    qtag = soup.find(text=re.compile(r"Q\d+"))
    if qtag:
        question_text = qtag.strip()
    else:
        # fallback: use entire visible text
        question_text = soup.get_text(" ", strip=True)

    # ------------------------------------------------------------
    # 3. Handle common question patterns
    # ------------------------------------------------------------

    # -----------------------------------------
    # Pattern A: "Download file ... sum of value column"
    # -----------------------------------------
    if "download" in question_text.lower() and "sum" in question_text.lower():
        return solve_download_and_sum(html, question_text), submit_url

    # -----------------------------------------
    # Pattern B: Contains a table, compute sum/avg/max/min
    # -----------------------------------------
    tables = soup.find_all("table")
    if tables:
        df = tables_to_dataframe(tables[0])
        numeric_cols = df.select_dtypes(include="number").columns
        if len(numeric_cols) >= 1:
            col = numeric_cols[0]

            if "sum" in question_text.lower():
                return float(df[col].sum()), submit_url
            if "average" in question_text.lower():
                return float(df[col].mean()), submit_url
            if "max" in question_text.lower():
                return float(df[col].max()), submit_url
            if "min" in question_text.lower():
                return float(df[col].min()), submit_url

        # fallback: return number of rows
        return int(len(df)), submit_url

    # -----------------------------------------
    # Pattern C: Yes/No questions
    # -----------------------------------------
    if "true or false" in question_text.lower():
        if "true" in question_text.lower():
            return True, submit_url
        return False, submit_url

    # -----------------------------------------
    # Pattern D: Simple numeric extraction
    # -----------------------------------------
    numbers = re.findall(r"\d+\.\d+|\d+", question_text)
    if len(numbers):
        return int(numbers[-1]), submit_url

    # -----------------------------------------
    # Final fallback: return entire text
    # -----------------------------------------
    return question_text, submit_url


# =====================================================================
#   HELPERS
# =====================================================================

def solve_download_and_sum(html: str, question: str):
    """
    Example quiz:
        "Download file. What is the sum of the 'value' column?"

    Handles:
    - finding the link
    - downloading the file
    - opening CSV/XLSX/PDF
    - computing requested sum
    """

    soup = BeautifulSoup(html, "html.parser")

    link = soup.find("a", href=True)
    if not link:
        raise ValueError("No download link found for file-based question.")

    file_url = link["href"]

    # download file
    resp = requests.get(file_url)
    filename = "temp_download"

    # try CSV
    try:
        df = pd.read_csv(io.BytesIO(resp.content))
        return float(df[df.columns[0]].sum())  # default: first column
    except Exception:
        pass

    # try Excel
    try:
        df = pd.read_excel(io.BytesIO(resp.content))
        return float(df[df.columns[0]].sum())
    except Exception:
        pass

    # try PDF text extraction
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            nums = re.findall(r"\d+\.\d+|\d+", text)
            return sum(map(float, nums))
    except Exception:
        pass

    raise ValueError("Could not process downloaded file.")


def tables_to_dataframe(table_tag):
    """
    Converts an HTML table to pandas DataFrame.
    """
    rows = []
    for row in table_tag.find_all("tr"):
        cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
        rows.append(cells)

    # fix irregular rows
    max_len = max(len(r) for r in rows)
    rows = [r + [""] * (max_len - len(r)) for r in rows]

    df = pd.DataFrame(rows[1:], columns=rows[0])
    return coerce_numeric_columns(df)


def coerce_numeric_columns(df: pd.DataFrame):
    """
    Convert numeric-looking columns to numeric dtype.
    """
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")
    return df
