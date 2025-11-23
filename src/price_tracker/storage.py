"""Storage layer for product configuration and price history.

Responsibilities:
- Persist product configurations (URLs, target prices, etc.).
- Store price history snapshots (product_id, timestamp, price).
- Provide a simple abstraction that can be implemented using:
  - SQLite via the built-in :mod:`sqlite3` module (preferred), or
  - CSV files as a simpler, fallback option.

This implementation uses SQLite and stores data in a local database
file. It supports the operations described in the "Database / Storage
Layer" section of the project document.
"""

import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

_DB_PATH = "price_tracker.db"


def _get_connection() -> sqlite3.Connection:
    """Create a new SQLite connection using the configured database path."""

    return sqlite3.connect(_DB_PATH)


def initialize_storage(db_path: Optional[str] = None) -> None:
    """Initialize the storage backend.

    This function creates the necessary SQLite tables if they do not
    already exist. It should be called once at application startup.

    Args:
        db_path (Optional[str]): Optional path to the SQLite database file.
            If omitted, a default file name is used in the current
            working directory.
    """

    global _DB_PATH
    if db_path:
        _DB_PATH = db_path

    conn = _get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_url TEXT NOT NULL,
            target_price REAL NOT NULL,
            site_name TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            scraped_at TEXT NOT NULL,
            price REAL NOT NULL,
            currency TEXT,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        """
    )

    # Migration helper: older versions used a ``timestamp`` column name.
    # If such a column exists, rename it to ``scraped_at`` so that the
    # schema matches the mini-project documentation.
    cur.execute("PRAGMA table_info(price_history)")
    columns = [row[1] for row in cur.fetchall()]
    if "scraped_at" not in columns and "timestamp" in columns:
        cur.execute("ALTER TABLE price_history RENAME COLUMN timestamp TO scraped_at")

    conn.commit()
    conn.close()


def save_product(product: Dict[str, Any]) -> int:
    """Save a product configuration to storage.

    Args:
        product (Dict[str, Any]): Product configuration with fields such as
            ``id``, ``product_url``, ``target_price``, ``site_name``,
            and ``active``.

    Returns:
        int: The unique ID of the stored product.
    """

    conn = _get_connection()
    cur = conn.cursor()

    active_flag = 1 if product.get("active", True) else 0
    now = datetime.utcnow().isoformat()

    if product.get("id") is not None:
        # Basic update path if an ID is supplied.
        cur.execute(
            """
            UPDATE products
            SET product_url = ?, target_price = ?, site_name = ?, active = ?
            WHERE id = ?
            """,
            (
                product["product_url"],
                float(product["target_price"]),
                product.get("site_name"),
                active_flag,
                int(product["id"]),
            ),
        )
        product_id = int(product["id"])
    else:
        cur.execute(
            """
            INSERT INTO products (product_url, target_price, site_name, active, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                product["product_url"],
                float(product["target_price"]),
                product.get("site_name"),
                active_flag,
                now,
            ),
        )
        product_id = int(cur.lastrowid)

    conn.commit()
    conn.close()
    return product_id


def list_products(active_only: bool = True) -> List[Dict[str, Any]]:
    """List stored product configurations.

    Args:
        active_only (bool): If True, return only active products.

    Returns:
        List[Dict[str, Any]]: A list of product configuration dictionaries
        matching the structure described in the project document.
    """

    conn = _get_connection()
    cur = conn.cursor()

    query = "SELECT id, product_url, target_price, site_name, active, created_at FROM products"
    params: List[Any] = []
    if active_only:
        query += " WHERE active = 1"

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    products: List[Dict[str, Any]] = []
    for row in rows:
        prod = {
            "id": row[0],
            "product_url": row[1],
            "target_price": row[2],
            "site_name": row[3],
            "active": bool(row[4]),
            "created_at": row[5],
        }
        products.append(prod)

    return products


def save_price_snapshot(
    product_id: int,
    price: float,
    currency: str = "INR",
    scraped_at: Optional[Any] = None,
) -> None:
    """Save a snapshot of a product's price.

    Args:
        product_id (int): Identifier of the product.
        price (float): Current price of the product.
        currency (str): Optional currency code (e.g. "INR").
        scraped_at (Optional[Any]): Optional timestamp. If not provided,
            the current UTC time is used.

    The record includes a simple currency field; for this mini-project
    implementation, a default value such as "INR" is used.
    """

    if scraped_at is None:
        scraped_at = datetime.utcnow().isoformat()

    conn = _get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO price_history (product_id, scraped_at, price, currency)
        VALUES (?, ?, ?, ?)
        """,
        (product_id, str(scraped_at), float(price), currency),
    )
    conn.commit()
    conn.close()


def get_price_history(product_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieve historical price records for a product.

    Args:
        product_id (int): Identifier of the product.
        limit (Optional[int]): Optional maximum number of history records
            to return.

    Returns:
        List[Dict[str, Any]]: A list of price history entries, each with
        at least ``timestamp``, ``price``, and ``currency``.
    """

    conn = _get_connection()
    cur = conn.cursor()

    query = (
        "SELECT id, product_id, scraped_at, price, currency "
        "FROM price_history WHERE product_id = ? ORDER BY scraped_at DESC"
    )
    params: List[Any] = [product_id]
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    history: List[Dict[str, Any]] = []
    for row in rows:
        entry = {
            "id": row[0],
            "product_id": row[1],
            "scraped_at": row[2],
            "price": row[3],
            "currency": row[4],
        }
        history.append(entry)

    return history


def add_product(
    product_url: str,
    target_price: float,
    site_name: Optional[str] = None,
    active: bool = True,
) -> int:
    """Create a new product record.

    This helper mirrors the ``add_product`` operation described in the
    "Database Layer" section of the mini-project document.
    """

    product: Dict[str, Any] = {
        "id": None,
        "product_url": product_url,
        "target_price": target_price,
        "site_name": site_name,
        "active": active,
    }
    return save_product(product)


def get_all_products(active_only: Optional[bool] = None) -> List[Dict[str, Any]]:
    """Return all stored products, optionally filtered by active flag."""

    if active_only is None:
        return list_products(active_only=False)
    return list_products(active_only=active_only)


def set_product_active(product_id: int, active: bool) -> None:
    """Set the ``active`` flag for a product.

    This helper is used by the CLI to toggle tracking on or off for a
    given product.
    """

    conn = _get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE products SET active = ? WHERE id = ?",
        (1 if active else 0, product_id),
    )
    conn.commit()
    conn.close()


def add_price_snapshot(
    product_id: int,
    price: float,
    currency: str = "INR",
    scraped_at: Optional[Any] = None,
) -> None:
    """Insert a price history entry for a product.

    This function is the high-level counterpart of
    :func:`save_price_snapshot` requested in the "Database Layer"
    description. It delegates to :func:`save_price_snapshot` while
    exposing the parameters explicitly.
    """

    save_price_snapshot(
        product_id=product_id,
        price=price,
        currency=currency,
        scraped_at=scraped_at,
    )


def get_latest_price(product_id: int) -> Optional[Dict[str, Any]]:
    """Return the most recent price snapshot for a product.

    Returns:
        Optional[Dict[str, Any]]: The latest record, or ``None`` if no
        history exists.
    """

    conn = _get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, product_id, scraped_at, price, currency
        FROM price_history
        WHERE product_id = ?
        ORDER BY scraped_at DESC
        LIMIT 1
        """,
        (product_id,),
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "product_id": row[1],
        "scraped_at": row[2],
        "price": row[3],
        "currency": row[4],
    }


def get_min_max_avg_price(product_id: int) -> Optional[Dict[str, Any]]:
    """Compute min, max, and average price for a product.

    This function supports the "view stored price history for trend
    insights" and "analyze price trends" scope in the project
    documentation.
    """

    conn = _get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT MIN(price), MAX(price), AVG(price), COUNT(*)
        FROM price_history
        WHERE product_id = ?
        """,
        (product_id,),
    )
    row = cur.fetchone()
    conn.close()

    if row is None or row[3] == 0:
        return None

    return {
        "min_price": row[0],
        "max_price": row[1],
        "avg_price": row[2],
        "count": row[3],
    }


def get_price_trend_direction(product_id: int, window: int = 5) -> str:
    """Estimate the recent price trend direction for a product.

    Args:
        product_id (int): Product identifier.
        window (int): Number of most recent records to consider.

    Returns:
        str: ``"up"``, ``"down"``, or ``"stable"`` based on how the
        latest price compares to the oldest price in the selected window.
    """

    if window <= 1:
        window = 2

    history = get_price_history(product_id, limit=window)
    if len(history) < 2:
        return "stable"

    # get_price_history returns newest first; reverse to chronological.
    history = list(reversed(history))
    first = float(history[0]["price"])
    last = float(history[-1]["price"])

    if first == 0:
        threshold = 0.01
    else:
        threshold = max(abs(first) * 0.01, 0.01)

    delta = last - first
    if delta > threshold:
        return "up"
    if delta < -threshold:
        return "down"
    return "stable"


def export_price_history_plot(
    product_id: int,
    output_path: str,
    limit: Optional[int] = None,
) -> None:
    """Optional helper: save a line chart of price vs time as a PNG.

    This supports the "visualize data" part of the methodology section.
    It uses :mod:`matplotlib` if available; otherwise it raises a
    :class:`RuntimeError` with an explanatory message.
    """

    try:
        import matplotlib.pyplot as plt  # type: ignore
        import matplotlib.dates as mdates  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "matplotlib is required to export price history plots."
        ) from exc

    history = get_price_history(product_id, limit=limit)
    if not history:
        raise RuntimeError("No price history available to plot.")

    from datetime import datetime as _dt

    times = [_dt.fromisoformat(entry["scraped_at"]) for entry in history]
    prices = [float(entry["price"]) for entry in history]

    plt.figure(figsize=(8, 4))
    plt.plot(times, prices, marker="o")
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.title(f"Price History for Product {product_id}")
    plt.grid(True)
    plt.gcf().autofmt_xdate()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d\n%H:%M"))
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
