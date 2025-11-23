"""End-to-end demo script for the Automated Price Tracker project.

This module runs a small demonstration that:
- initializes the storage layer,
- adds one or two sample products,
- performs a single scrape + analyze + notify cycle,
- prints previous vs new prices and whether a notification is (or would be) sent.

It is intended for quick manual demonstration during project review.
"""

import os
from typing import List

from .notifier import send_price_drop_email
from .price_analyzer import analyze_price
from .scraper import ScraperError, get_product_info
from .storage import (
    add_price_snapshot,
    add_product,
    get_latest_price,
    initialize_storage,
)


def run_demo() -> None:
    print("=== Automated Price Tracker: Demo Run ===")
    print(
        "This demo adds a couple of sample products, fetches their current prices,\n"
        "compares them with target prices, stores a snapshot, and shows whether\n"
        "an email notification would be sent (if email is configured).\n"
    )

    initialize_storage()

    samples: List[dict] = [
        {
            "url": "https://www.amazon.in/dp/B0C7H1MCYH",  # example URL
            "site": "amazon",
            "target_price": 50000.0,
        },
        {
            "url": "https://www.flipkart.com/",  # example home page
            "site": "flipkart",
            "target_price": 1000.0,
        },
    ]

    recipient = os.getenv("ALERT_RECIPIENT_EMAIL") or os.getenv("ALERT_EMAIL")

    for idx, sample in enumerate(samples, start=1):
        print()
        print(f"--- Demo product {idx} ---")
        url = sample["url"]
        site = sample["site"]
        target_price = float(sample["target_price"])

        product_id = add_product(product_url=url, target_price=target_price, site_name=site)

        previous = get_latest_price(product_id)
        if previous is not None:
            print(
                "Previous recorded price:",
                previous.get("price"),
                "at",
                previous.get("scraped_at"),
            )
        else:
            print("No previous price recorded for this product.")

        try:
            info = get_product_info(url, site)
        except ScraperError as exc:
            print(f"Error while scraping demo product: {exc}")
            continue

        name = info.get("product_name", "Unknown product")
        current_price = float(info.get("current_price", 0.0))
        print("Product name:", name)
        print("Current price:", current_price)
        print("Target price:", target_price)

        add_price_snapshot(product_id=product_id, price=current_price)

        analysis = analyze_price(current_price=current_price, target_price=target_price)
        print("Price difference (current - target):", analysis["difference"])

        if analysis["is_below_or_equal"]:
            print("Condition met: current price is at or below target.")
            if recipient:
                sent = send_price_drop_email(
                    user_email=recipient,
                    product_name=name,
                    product_url=url,
                    current_price=current_price,
                    target_price=target_price,
                    config_path=None,
                )
                print("Notification sent:", bool(sent))
            else:
                print(
                    "Email recipient not configured (ALERT_RECIPIENT_EMAIL). "
                    "In a full run, this is where an email would be sent."
                )
        else:
            print("Condition not met: no notification would be sent.")

    print()
    print("Demo finished. You can inspect the database for stored price history.")


if __name__ == "__main__":
    run_demo()
