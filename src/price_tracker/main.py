"""Entry point for the modular Automated Price Tracker and Notifier project.

This module now provides a simple console-based menu that demonstrates
the integration between the "User Input", "Web Scraper Module", and
"Database / Storage Layer" described in the project document.

Current features:
- Menu with options to add a product, list tracked products, or exit.
- When a product is added, the program immediately:
  - validates the user input,
  - scrapes the product page using the scraper module,
  - prints the extracted product name and current price,
  - stores both the product configuration and an initial price snapshot
    in the SQLite-backed storage layer.
"""

from typing import Dict, List

from .input_module import prompt_product_from_cli
from .scheduler_module import schedule_price_checks
from .scraper import ScraperError, get_product_info
from .storage import (
    get_min_max_avg_price,
    get_price_history,
    get_price_trend_direction,
    initialize_storage,
    list_products,
    save_price_snapshot,
    save_product,
    set_product_active,
)


def _add_product_flow() -> None:
    """Handle the "Add product" menu option.

    This function corresponds to the demo flow requested in the
    methodology: the user enters a product link and desired price, the
    program fetches the webpage, extracts the product name and price,
    prints them, and stores the result.
    """

    product: Dict = prompt_product_from_cli()
    product_id = save_product(product)

    print("\nFetching product details...")
    try:
        info = get_product_info(product["product_url"], product["site_name"])
    except ScraperError as exc:
        print(f"Error while scraping product: {exc}")
        return

    name = info["product_name"]
    current_price = float(info["current_price"])

    print("Product added successfully.")
    print(f"Product ID: {product_id}")
    print(f"Product name: {name}")
    print(f"Current price: {current_price}")

    save_price_snapshot(product_id=product_id, price=current_price)
    print("Initial price snapshot stored.\n")


def _list_products_flow() -> None:
    """Handle the "List all tracked products" menu option."""

    products: List[Dict] = list_products(active_only=False)
    if not products:
        print("No products are being tracked yet.\n")
        return

    print("Tracked products:")
    for prod in products:
        status = "active" if prod.get("active") else "inactive"
        print(
            f"- [ID {prod['id']}] {prod['product_url']} "
            f"(target={prod['target_price']}, site={prod['site_name']}, {status})"
        )
    print()


def _prompt_for_product_selection() -> Dict | None:
    """Display products and prompt the user to choose one by ID.

    Returns:
        Dict | None: The selected product dictionary, or ``None`` if the
        selection was invalid or no products exist.
    """

    products: List[Dict] = list_products(active_only=False)
    if not products:
        print("No products are being tracked yet.\n")
        return None

    print("Tracked products:")
    for prod in products:
        status = "active" if prod.get("active") else "inactive"
        print(
            f"- [ID {prod['id']}] {prod['product_url']} "
            f"(target={prod['target_price']}, site={prod['site_name']}, {status})"
        )

    raw_id = input("Enter product ID: ").strip()
    try:
        selected_id = int(raw_id)
    except ValueError:
        print("Invalid product ID.\n")
        return None

    for prod in products:
        if prod["id"] == selected_id:
            return prod

    print(f"No product found with ID {selected_id}.\n")
    return None


def _view_price_history_flow() -> None:
    """Handle the "View price history" menu option.

    Shows recent records and basic statistics (min, max, average) as
    well as a simple trend direction indicator (up/down/stable).
    """

    product = _prompt_for_product_selection()
    if product is None:
        return

    raw_n = input("How many recent records to show? (default 10): ").strip()
    limit = 10
    if raw_n:
        try:
            limit = max(1, int(raw_n))
        except ValueError:
            print("Invalid number, using default of 10.")

    history = get_price_history(product_id=product["id"], limit=limit)
    if not history:
        print("No price history for this product yet.\n")
        return

    print(
        f"\nRecent {len(history)} price records for product ID {product['id']}:"
    )
    for entry in history:
        scraped_at = entry.get("scraped_at")
        price = entry.get("price")
        currency = entry.get("currency") or ""
        print(f"- {scraped_at} -> {price} {currency}".rstrip())

    stats = get_min_max_avg_price(product["id"])
    if stats:
        print(
            f"\nStats over {stats['count']} records: "
            f"min={stats['min_price']}, "
            f"max={stats['max_price']}, "
            f"avg={stats['avg_price']:.2f}"
        )

    trend = get_price_trend_direction(product["id"])
    print(f"Trend direction (recent): {trend}\n")


def _toggle_product_active_flow() -> None:
    """Handle the "Toggle product active/inactive" menu option."""

    product = _prompt_for_product_selection()
    if product is None:
        return

    currently_active = bool(product.get("active"))
    new_status = not currently_active
    set_product_active(product_id=product["id"], active=new_status)

    label = "active" if new_status else "inactive"
    print(f"Product ID {product['id']} is now {label}.\n")


def _start_monitoring_flow() -> None:
    print()
    print("Automatic price monitoring will keep running until you press Ctrl+C.")
    raw_interval = input(
        "Enter check interval in minutes (press Enter for default 60): "
    ).strip()
    interval = 60
    if raw_interval:
        try:
            interval = max(1, int(raw_interval))
        except ValueError:
            print("Invalid interval, using default of 60 minutes.")

    schedule_price_checks(interval_minutes=interval, job_function=None, use_schedule_library=True)


def main() -> None:
    """Entry point for the modular price tracker CLI.

    Presents a simple console menu:

    1. Add a product (URL + target price)
    2. List all tracked products
    3. View price history for a product
    4. Toggle product active/inactive
    5. Start automatic price monitoring
    6. Exit
    """

    initialize_storage()

    while True:
        print("Automated Price Tracker and Notifier")
        print("1. Add a product")
        print("2. List all tracked products")
        print("3. View price history for a product")
        print("4. Toggle product active/inactive")
        print("5. Start automatic price monitoring")
        print("6. Exit")
        choice = input("Select an option (1-6): ").strip()

        if choice == "1":
            _add_product_flow()
        elif choice == "2":
            _list_products_flow()
        elif choice == "3":
            _view_price_history_flow()
        elif choice == "4":
            _toggle_product_active_flow()
        elif choice == "5":
            _start_monitoring_flow()
        elif choice == "6":
            print("Exiting. Goodbye!")
            break
        else:
            print("Invalid option. Please enter a number between 1 and 6.\n")


if __name__ == "__main__":
    main()
