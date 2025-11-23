"""Basic smoke tests for the Automated Price Tracker project.

These tests use simple ``assert`` statements and can be run with::

    python tests_basic.py

They cover:
- scraper parsing with mocked HTML,
- price analyzer logic,
- storage layer insert/retrieve operations.
"""

import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


from price_tracker.price_analyzer import analyze_price
from price_tracker.scraper import parse_product_details
from price_tracker.storage import (
    add_price_snapshot,
    add_product,
    get_price_history,
    get_all_products,
    initialize_storage,
)


def test_analyze_price() -> None:
    result = analyze_price(90.0, 100.0)
    assert result["is_below_or_equal"] is True
    assert result["difference"] == -10.0

    result = analyze_price(100.0, 100.0)
    assert result["is_below_or_equal"] is True
    assert result["difference"] == 0.0

    result = analyze_price(120.0, 100.0)
    assert result["is_below_or_equal"] is False
    assert result["difference"] == 20.0


def test_scraper_generic_parser() -> None:
    html = """
    <html>
      <head><title>Demo Product</title></head>
      <body>
        <div>Only Rs. 1,234.00 today!</div>
      </body>
    </html>
    """
    details = parse_product_details(html, "other")
    assert details["product_name"] == "Demo Product"
    assert isinstance(details["current_price"], float)
    assert details["current_price"] > 0


def test_storage_roundtrip() -> None:
    db_path = "test_price_tracker.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    initialize_storage(db_path=db_path)

    product_id = add_product(
        product_url="http://example.com/demo-product",
        target_price=999.0,
        site_name="other",
        active=True,
    )

    products = get_all_products(active_only=None)
    assert any(p["id"] == product_id for p in products)

    add_price_snapshot(product_id=product_id, price=950.0)
    history = get_price_history(product_id=product_id)
    assert len(history) == 1
    assert history[0]["price"] == 950.0

    if os.path.exists(db_path):
        os.remove(db_path)


def main() -> None:
    test_analyze_price()
    test_scraper_generic_parser()
    test_storage_roundtrip()
    print("All basic tests passed.")


if __name__ == "__main__":
    main()
