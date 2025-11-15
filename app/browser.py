# app/browser.py

import os
from playwright.sync_api import sync_playwright


class Browser:
    """
    A thin wrapper around Playwright that:
    - launches Chromium headless
    - loads JS-rendered pages reliably (networkidle)
    - provides helper utilities for file downloading
    - extracts final rendered HTML
    """

    def __init__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        self.page = self.browser.new_page()

    def render_page(self, url: str) -> str:
        """
        Loads a webpage and returns the fully rendered HTML.
        This is required because the quiz pages use JavaScript dynamically.
        """
        self.page.goto(url, wait_until="networkidle")
        return self.page.content()

    def download_file(self, url: str, save_path: str) -> str:
        """
        Uses Playwright to download files triggered by navigating to a URL
        or clicking inside a page.
        """
        with self.page.expect_download() as dl_info:
            self.page.goto(url)
        download = dl_info.value
        download.save_as(save_path)
        return save_path

    def download_via_click(self, selector: str, save_path: str) -> str:
        """
        Example: clicking <a> or <button> that triggers file download.
        """
        with self.page.expect_download() as dl_info:
            self.page.click(selector)
        download = dl_info.value
        download.save_as(save_path)
        return save_path

    def get_text(self, selector: str):
        """Extract text content from any element."""
        return self.page.text_content(selector)

    def get_table_contents(self, selector: str):
        """
        Returns table content as list of rows, each row is list of cell values.
        Useful for quiz questions that involve reading tables.
        """
        rows = self.page.query_selector_all(f"{selector} tr")
        parsed = []
        for row in rows:
            cells = row.query_selector_all("td, th")
            parsed.append([c.text_content().strip() for c in cells])
        return parsed

    def close(self):
        """Gracefully close Playwright."""
        self.browser.close()
        self.playwright.stop()


# Optional convenience function
def fetch_rendered_html(url: str) -> str:
    """
    Simple helper function if you want to call this directly elsewhere.
    Automatically handles open → render → close.
    """
    b = Browser()
    html = b.render_page(url)
    b.close()
    return html
