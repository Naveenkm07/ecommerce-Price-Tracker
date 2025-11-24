"""Scraper module for fetching product information from e-commerce sites.

Responsibilities:
- Use :mod:`requests` to fetch HTML content for a given product URL.
- Use :class:`bs4.BeautifulSoup` to extract:
  - product name
  - current price
- Provide a pluggable design so that site-specific parsing logic can be
  added for:
  - Amazon
  - Flipkart
  - Generic/other sites
- Include basic error handling for:
  - network issues
  - unexpected HTML structure changes
  - invalid URLs

This module implements the "Web Scraper Module" part of the methodology
from the project document: after the user enters a product link, the
program fetches the webpage and extracts the product name and price.
"""

import re
from typing import Any, Dict, Tuple

import requests
from bs4 import BeautifulSoup


class ScraperError(Exception):
    """Raised when a product page cannot be fetched or parsed correctly."""


def fetch_product_page(url: str, timeout: int = 10) -> str:
    """Fetch the raw HTML content for a product page.

    A browser-like ``User-Agent`` header is sent to reduce the chance of
    the request being blocked by the server.

    Args:
        url (str): The product page URL.
        timeout (int): Network timeout in seconds.

    Returns:
        str: The HTML content of the page as a string.

    Raises:
        ScraperError: If the request fails or the server returns an
            unexpected status code.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ScraperError(f"Network error while fetching {url}: {exc}") from exc

    return response.text


def _parse_price_text(price_text: str) -> float:
    """Extract a numeric price from a text string.

    This helper removes currency symbols and thousands separators, then
    parses the remaining digits into a floating-point number.

    Raises:
        ScraperError: If no digits can be found in the text.
    """
    # Find numeric-like sequences such as "1,234.56" or "1234" in the text.
    # This avoids picking up the dot from a token like "Rs." which led to
    # values like ".1234.00" after naive stripping.
    candidates = re.findall(r"\d[\d,.]*", price_text)
    if not candidates:
        raise ScraperError(f"Could not parse price from text: {price_text!r}")

    # Prefer the longest candidate (most complete number on the line)
    token = max(candidates, key=len)
    # Remove thousands separators
    token = token.replace(",", "")
    # Normalize multiple dots to a single decimal point
    if token.count(".") > 1:
        head, tail = token.split(".", 1)
        tail = tail.replace(".", "")
        token = head + "." + tail

    try:
        return float(token)
    except ValueError as exc:
        raise ScraperError(f"Could not parse price from text: {price_text!r}") from exc


def _parse_amazon_product(soup: BeautifulSoup) -> Tuple[str, float]:
    """Parse product details from an Amazon product page.

    The selectors here assume a typical Amazon HTML structure (e.g.
    ``id="productTitle"`` for the title and ``id="priceblock_ourprice"``
    or ``id="priceblock_dealprice"`` for the price).
    """

    name_el = soup.find(id="productTitle")
    price_el = soup.find(id="priceblock_ourprice") or soup.find(id="priceblock_dealprice")

    if not name_el or not price_el:
        raise ScraperError("Could not locate product name or price on Amazon page.")

    name = name_el.get_text(strip=True)
    price = _parse_price_text(price_el.get_text())
    return name, price


def _parse_flipkart_product(soup: BeautifulSoup) -> Tuple[str, float]:
    """Parse product details from a Flipkart product page.

    The selectors are based on a common Flipkart layout where:
    - the product name is in a ``span`` with class ``B_NuCI``
    - the price is in a ``div`` with class ``_30jeq3 _16Jk6d``
    """

    name_el = soup.find("span", {"class": "B_NuCI"})
    price_el = soup.find("div", {"class": "_30jeq3 _16Jk6d"})

    if not name_el or not price_el:
        raise ScraperError("Could not locate product name or price on Flipkart page.")

    name = name_el.get_text(strip=True)
    price = _parse_price_text(price_el.get_text())
    return name, price


def _parse_generic_product(soup: BeautifulSoup) -> Tuple[str, float]:
    """Best-effort parser for generic e-commerce pages.

    - Uses the document ``<title>`` as the product name, if available.
    - Looks for the first piece of text that appears to contain a price
      (e.g. includes a currency symbol or digits).
    """

    title_el = soup.find("title")
    name = title_el.get_text(strip=True) if title_el else "Unknown product"

    # Try to find the first reasonable price-like text.
    text_candidates = soup.find_all(string=re.compile(r"[0-9]"))
    for candidate in text_candidates:
        text = candidate.strip()
        if not text:
            continue
        try:
            price = _parse_price_text(text)
            return name, price
        except ScraperError:
            continue

    raise ScraperError("Could not find a price on the page.")


def parse_product_details(html: str, site_name: str) -> Dict[str, Any]:
    """Parse product details from HTML for a specific site.

    Args:
        html (str): Raw HTML content of the product page.
        site_name (str): Identifier for the e-commerce site, such as
            ``"amazon"``, ``"flipkart"``, or ``"other"``.

    Returns:
        Dict[str, Any]: A dictionary containing at least:
            - ``"product_name"``
            - ``"current_price"``

    Raises:
        ScraperError: If parsing fails for any reason.
    """

    soup = BeautifulSoup(html, "html.parser")
    site = (site_name or "").strip().lower()

    if site == "amazon":
        name, price = _parse_amazon_product(soup)
    elif site == "flipkart":
        name, price = _parse_flipkart_product(soup)
    else:
        name, price = _parse_generic_product(soup)

    return {"product_name": name, "current_price": price}


def get_product_info(url: str, site_name: str) -> Dict[str, Any]:
    """High-level function to obtain product information.

    This function performs the two core steps described in the project
    methodology:

    1. Fetch the page HTML for the given URL using :func:`fetch_product_page`.
    2. Parse the HTML using :func:`parse_product_details`.

    Args:
        url (str): Product page URL.
        site_name (str): Site identifier (e.g., ``"amazon"``, ``"flipkart"``).

    Returns:
        Dict[str, Any]: Parsed product information including at least name,
        price, and the original URL and site name for convenience.
    """

    html = fetch_product_page(url)
    details = parse_product_details(html, site_name)
    details["product_url"] = url
    details["site_name"] = site_name
    return details


def scrape_product(product_url: str, site_name: str) -> Tuple[str, float]:
    """Convenience wrapper for scraping a single product.

    Args:
        product_url (str): Product page URL.
        site_name (str): Site identifier, forwarded to
            :func:`parse_product_details`.

    Returns:
        Tuple[str, float]: ``(product_name, current_price)``.

    Raises:
        ScraperError: If fetching or parsing fails.
    """

    info = get_product_info(product_url, site_name)
    return info["product_name"], float(info["current_price"])
