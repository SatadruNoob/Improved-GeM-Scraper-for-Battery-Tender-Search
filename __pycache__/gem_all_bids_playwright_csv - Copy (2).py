# file: gem_all_bids_playwright_csv.py
# FINAL VERSION WITH BID-NO HASH IDENTITY + NEW TODAY FLAG

import sys
import os
import time
import hashlib
from pathlib import Path
from datetime import datetime

import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError

print("SCRAPER CWD:", os.getcwd())

# -------------------------------------------------
# Resolve BASE directory (exe-aware)
# -------------------------------------------------
if getattr(sys, "frozen", False):
    INTERNAL_DIR = Path(sys._MEIPASS)
else:
    INTERNAL_DIR = Path(__file__).parent

BASE_DIR = INTERNAL_DIR
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

START_URL = "https://bidplus.gem.gov.in/all-bids"
CSV_FILE = DATA_DIR / "gem_all_bids.csv"

PAGE_DELAY_SEC = 1.5
MAX_NEXT_MISSES = 2

DEBUG_DIR = BASE_DIR / "debug_artifacts"
DEBUG_DIR.mkdir(exist_ok=True)

LOG_FILE = DATA_DIR / "scrape_status.log"

SEARCH_KEYWORD = "batter"
RUN_DATE = datetime.now().strftime("%Y-%m-%d")

# -------------------------------------------------
# Logging helpers
# -------------------------------------------------
def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

    try:
        print(line)
    except OSError:
        pass


def dump_debug(page, page_index, reason):
    prefix = DEBUG_DIR / f"page_{page_index}_{reason}"
    page.screenshot(path=f"{prefix}.png", full_page=True)
    with open(f"{prefix}.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    log(f"[debug] Dumped DOM + screenshot: {prefix}")

# -------------------------------------------------
# Identity Hash Helpers (Bid-No ONLY)
# -------------------------------------------------
def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def compute_identity_hash(bid_no: str) -> str:
    return sha256(bid_no.strip())

# -------------------------------------------------
# Extraction
# -------------------------------------------------
def extract_bids(page):
    bids = []
    cards = page.locator("div.card")
    count = cards.count()

    for i in range(count):
        card = cards.nth(i)

        bid_links = card.locator(".bid_no_hover")
        if bid_links.count() == 0:
            continue

        bid_no = bid_links.first.inner_text().strip()

        # ---------------- Items extraction ----------------
        items = ""
        items_block = card.locator("strong:has-text('Items:')").locator("..")

        if items_block.count():
            a_tag = items_block.locator("a")
            if a_tag.count():
                dc = a_tag.first.get_attribute("data-content")
                if dc:
                    items = dc.strip()
                else:
                    txt = a_tag.first.text_content()
                    if txt and txt.strip().lower() != "view":
                        items = txt.strip()

            if not items:
                raw = items_block.evaluate("el => el.textContent")
                if raw:
                    items = raw.replace("Items:", "").strip()

        quantity_el = card.locator("strong:has-text('Quantity:')").locator("..")
        quantity = quantity_el.inner_text().replace("Quantity:", "").strip()

        dept_block = card.locator("div.col-md-5 .row").nth(1)
        department = dept_block.inner_text().replace("\n", " | ").strip()

        start_date = card.locator(".start_date").inner_text().strip()
        end_date = card.locator(".end_date").inner_text().strip()

        bids.append({
            "Bid No": bid_no,
            "Items": items,
            "Quantity": quantity,
            "Department Name And Address": department,
            "Start Date": start_date,
            "End Date": end_date,
        })

        if not items:
            log(f"[WARN] Items missing for Bid {bid_no}")

    return bids

# -------------------------------------------------
# CSV helpers
# -------------------------------------------------
def append_to_csv(rows):
    if not rows:
        return

    df = pd.DataFrame(rows)
    write_header = not CSV_FILE.exists()
    df.to_csv(CSV_FILE, mode="a", index=False, header=write_header)

def load_seen_hashes():
    if not CSV_FILE.exists():
        return set()

    df = pd.read_csv(CSV_FILE)

    # Backward compatibility
    if "Identity Hash" not in df.columns:
        df["Identity Hash"] = df["Bid No"].astype(str).apply(compute_identity_hash)

    return set(df["Identity Hash"].astype(str))

# -------------------------------------------------
# Main
# -------------------------------------------------
def main():
    seen_hashes = load_seen_hashes()
    page_index = 1
    next_misses = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        log("Opening GeM All Bids…")
        page.goto(START_URL, timeout=90_000)

        try:
            page.wait_for_selector("div.card", timeout=60_000)
        except TimeoutError:
            dump_debug(page, page_index, "initial_load_failed")
            return

        # ---------------- Keyword Search ----------------
        try:
            log(f"[SEARCH] Applying keyword filter: {SEARCH_KEYWORD}")

            search_box = page.locator("#searchBid")
            search_box.wait_for(timeout=30_000)

            search_box.fill("")
            search_box.type(SEARCH_KEYWORD, delay=100)
            search_box.press("Enter")

            page.wait_for_timeout(1500)
            page.wait_for_selector("div.card", timeout=60_000)

            log(f"[SEARCH] Cards after filter: {page.locator('div.card').count()}")

        except TimeoutError:
            dump_debug(page, page_index, "search_failed")
            log("[FATAL] Keyword search failed")
            return

        # ---------------- Scraping Loop ----------------
        try:
            while True:
                log(f"[heartbeat] page={page_index}")

                cards_count = page.locator("div.card").count()
                log(f"[debug] cards_found={cards_count}")

                if cards_count == 0:
                    dump_debug(page, page_index, "no_cards")
                    break

                bids = extract_bids(page)
                buffer = []

                for bid in bids:
                    identity_hash = compute_identity_hash(bid["Bid No"])

                    if identity_hash in seen_hashes:
                        bid["New Today"] = "NO"
                    else:
                        bid["New Today"] = "YES"
                        seen_hashes.add(identity_hash)

                    bid["Identity Hash"] = identity_hash
                    bid["First Seen Date"] = RUN_DATE

                    buffer.append(bid)

                log(f"[+] Processed {len(buffer)} bids")
                append_to_csv(buffer)

                # ---------------- Pagination ----------------
                next_btn = page.locator("#light-pagination .next:not(.current)")

                if next_btn.count() == 0:
                    next_misses += 1
                    log(f"[WARN] Next button missing ({next_misses}/{MAX_NEXT_MISSES})")

                    if next_misses >= MAX_NEXT_MISSES:
                        dump_debug(page, page_index, "next_missing")
                        log("[STOP] Pagination ended")
                        break

                    time.sleep(2)
                    continue

                next_misses = 0

                first_bid = page.locator(".bid_no_hover").first.inner_text()
                next_btn.click()
                time.sleep(PAGE_DELAY_SEC)

                try:
                    page.wait_for_function(
                        """
                        (prev) => {
                            const el = document.querySelector('.bid_no_hover');
                            return el && el.innerText !== prev;
                        }
                        """,
                        arg=first_bid,
                        timeout=60_000,
                    )
                except TimeoutError:
                    dump_debug(page, page_index, "dom_timeout")
                    continue

                page_index += 1

        except Exception as e:
            import traceback
            log(f"[FATAL] Main loop crash: {e}")
            log(traceback.format_exc())
            dump_debug(page, page_index, "main_loop_crash")

        browser.close()

    log("[✓] Scraping finished")

# -------------------------------------------------
if __name__ == "__main__":
    main()
