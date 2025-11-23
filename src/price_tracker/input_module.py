"""Input module for collecting product URLs and target prices from the user.

Responsibilities:
- Provide a simple CLI / text-based interface for entering products to track.
- Represent each tracked product as a Python object or dictionary with fields:
  - id
  - product_url
  - target_price
  - site_name (e.g., "amazon", "flipkart", "other")
  - active (boolean flag)

This module implements the "User Input" part of the methodology described
in the project document: the user enters a product link and desired price,
which are validated before being passed to the rest of the system.
"""

from typing import Dict, List


def _validate_url(url: str) -> str:
    """Validate that the URL is non-empty and starts with http/https.

    Args:
        url (str): Raw URL string entered by the user.

    Returns:
        str: A cleaned and validated URL.

    Raises:
        ValueError: If the URL is empty or does not start with http/https.
    """
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty.")
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("URL must start with http:// or https://.")
    return url


def _validate_target_price(raw_value: str) -> float:
    """Validate and parse the target price as a positive number.

    This helper encapsulates the requirement that the target price should
    be a positive number, as stated in the project specification.
    """
    value = float(raw_value)
    if value <= 0:
        raise ValueError("Target price must be a positive number.")
    return value


def _normalize_site_name(raw_site: str) -> str:
    """Normalise the site name string for internal use.

    Args:
        raw_site (str): Site name entered by the user.

    Returns:
        str: Lowercase site identifier such as "amazon", "flipkart", or
        "other".
    """
    site = raw_site.strip().lower()
    if site not in {"amazon", "flipkart", "other"}:
        site = "other"
    return site


def prompt_product_from_cli() -> Dict:
    """Interactively collect details for a single product from the user.

    This function provides the console-based input flow described in the
    "User Input" / methodology section of the mini-project document. It
    validates the product URL and target price before returning.

    Returns:
        Dict: A product configuration dictionary with keys:
            - "id" (None for new products; the storage layer will assign one)
            - "product_url"
            - "target_price"
            - "site_name"
            - "active" (bool)
    """
    while True:
        try:
            url = _validate_url(input("Enter product URL: "))
            break
        except ValueError as exc:
            print(f"Invalid URL: {exc}")

    while True:
        raw_price = input("Enter target price (positive number): ")
        try:
            target_price = _validate_target_price(raw_price)
            break
        except ValueError as exc:
            print(f"Invalid price: {exc}")

    site_raw = input('Enter site name (e.g., "amazon", "flipkart", "other"): ')
    site_name = _normalize_site_name(site_raw)

    product: Dict = {
        "id": None,
        "product_url": url,
        "target_price": target_price,
        "site_name": site_name,
        "active": True,
    }
    return product


def get_user_products() -> List[Dict]:
    """Collect one or more product configurations from the user.

    This helper function loops over :func:`prompt_product_from_cli` to allow
    the user to enter multiple products in one run. It is primarily useful
    for testing the input module in isolation; the main CLI menu uses the
    same validation logic but a different control flow.
    """
    products: List[Dict] = []
    while True:
        product = prompt_product_from_cli()
        products.append(product)
        again = input("Add another product? (y/n): ").strip().lower()
        if again != "y":
            break
    return products
