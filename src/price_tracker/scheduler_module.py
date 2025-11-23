"""Scheduler module for periodic price checks.

Responsibilities:
- Schedule recurring tasks that:
  - Load active products from storage.
  - Call the scraper to fetch current prices.
  - Use the analyzer to decide whether to notify.
  - Save price history snapshots.
  - Trigger notifications when conditions are met.
- Use the `schedule` library (preferred) or a custom loop with `time.sleep`.

Note: This file currently contains only function definitions and docstrings.
"""

import os
import time
from datetime import datetime
from typing import Callable, Optional

import schedule

from .notifier import send_price_drop_email
from .price_analyzer import analyze_price
from .scraper import ScraperError, get_product_info
from .storage import add_price_snapshot, get_all_products


def _run_price_check_once() -> None:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print()
    print(f"[Scheduler] Running price check at {now}")

    try:
        products = get_all_products(active_only=True)
    except Exception as exc:
        print(f"[Scheduler] Failed to load products: {exc}")
        return

    if not products:
        print("[Scheduler] No active products to process.")
        return

    processed = 0
    successful_scrapes = 0
    notifications_sent = 0

    recipient_email = os.getenv("ALERT_RECIPIENT_EMAIL") or os.getenv("ALERT_EMAIL")

    for product in products:
        processed += 1
        url = product.get("product_url", "")
        site = product.get("site_name") or "other"

        print(f"[Scheduler] Checking product ID {product.get('id')} ({url})")

        try:
            info = get_product_info(url, site)
        except ScraperError as exc:
            print(f"[Scheduler] Scraper error for {url}: {exc}")
            continue
        except Exception as exc:
            print(f"[Scheduler] Unexpected error while scraping {url}: {exc}")
            continue

        try:
            current_price = float(info["current_price"])
        except Exception:
            print(f"[Scheduler] Invalid price data for {url}")
            continue

        successful_scrapes += 1
        add_price_snapshot(product_id=product["id"], price=current_price)

        target_price = float(product.get("target_price", 0))
        analysis = analyze_price(current_price=current_price, target_price=target_price)

        print(
            f"[Scheduler] Current price = {current_price}, target = {target_price}, "
            f"diff = {analysis['difference']}"
        )

        if analysis.get("is_below_or_equal") and recipient_email:
            sent = send_price_drop_email(
                user_email=recipient_email,
                product_name=info.get("product_name", "Unknown product"),
                product_url=url,
                current_price=current_price,
                target_price=target_price,
                config_path=None,
            )
            if sent:
                notifications_sent += 1
                print("[Scheduler] Notification sent via email.")
            else:
                print("[Scheduler] Email notification skipped or failed.")
        elif analysis.get("is_below_or_equal") and not recipient_email:
            print("[Scheduler] ALERT_RECIPIENT_EMAIL not configured; cannot send email.")

    print(
        f"[Scheduler] Run summary: processed={processed}, "
        f"successful_scrapes={successful_scrapes}, "
        f"notifications_sent={notifications_sent}"
    )


def schedule_price_checks(
    interval_minutes: int,
    job_function: Optional[Callable[[], None]] = None,
    use_schedule_library: bool = True,
) -> None:
    """Set up periodic price check jobs.

    Args:
        interval_minutes (int): How often to run the job, in minutes.
        job_function (Callable[[], None] | None): A callable that performs
            the end-to-end price check workflow. If ``None``, a default
            implementation that loads products, scrapes, analyzes, stores,
            and notifies is used.
        use_schedule_library (bool): If True, configure the `schedule`
            library. If False, a custom loop with ``time.sleep`` is used.
    """

    if job_function is None:
        job_function = _run_price_check_once

    print(
        f"Starting periodic price checks every {interval_minutes} minute(s). "
        "Press Ctrl+C to stop."
    )

    if use_schedule_library:
        schedule.clear()
        schedule.every(interval_minutes).minutes.do(job_function)

        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nScheduler stopped.")
    else:
        try:
            while True:
                job_function()
                time.sleep(max(1, int(interval_minutes) * 60))
        except KeyboardInterrupt:
            print("\nScheduler stopped.")

