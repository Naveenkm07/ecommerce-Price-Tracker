# Ecommerce-Price-Tracker

**Ecommerce-Price-Tracker** is a python utility which notifies you when the price of the product on your wishlist is less than what you desired. It has support for price tracking on Amazon and Flipkart.

## Features
- Track prices of a product on Amazon
- Track prices of a product on Flipkart
- Track prices of a product on both Amazon and Flipkart simultaneously
- Get notified via emails when the price is lower than desired price

## Setup
To use the **Ecommerce-Price-Tracker**, you just need the product name, product url and the desired price.

* Product name - The name of the product you want to track
* Product URL - The URL of the product page on Amazon or Flipkart
* Desired price - The least price you want to buy the product at. When this price will be lower or eqaul to the actual price of the product, you'll be notified via a email.

**Also provide your email and email password in the `credentials.json` file, and enable less secure apps on your email service provider before running the program.**

## Dependencies
*External modules used:*
- beautifulsoup4
- helium
- requests 
- validators 
- html5lib 

Download all the above mentioned modules at once by executing the command `pip install -r requirements.txt` on the terminal.


## Installation
### Using Git
Type the following command in your Git Bash:

- For SSH:
```git clone git@github.com:shravanasati/Ecommerce-Price-Tracker.git```
- For HTTPS: ```git clone https://github.com/shravanasati/Ecommerce-Price-Tracker.git```

The whole repository would be cloned in the directory you opened the Git Bash in.

### Using GitHub ZIP download
You can alternatively download the repository as a zip file using the
GitHub **Download ZIP** feature by clicking [here](https://github.com/shravanasati/Ecommerce-Price-Tracker/archive/master.zip).

## Mini-project: Automated Price Tracker and Notifier (Modular Version)

This repository also contains a modular implementation that follows the
"Automated Price Tracker and Notifier Using Python" mini-project
specification from the college document. The modular version is
organised as a Python package under `src/`.

### Project structure (modular mini-project)

- `src/`
  - `price_tracker/`
    - `__init__.py`
    - `input_module.py` (CLI input and validation)
    - `scraper.py` (requests + BeautifulSoup parsing for Amazon, Flipkart, generic)
    - `price_analyzer.py` (compare current vs target price)
    - `notifier.py` (email notifier + SMS/push stubs)
    - `storage.py` (SQLite products + price history, trend helpers)
    - `scheduler_module.py` (periodic checks using `schedule`)
    - `main.py` (console menu)
    - `demo.py` (end-to-end demo run)

### Objectives (modular version)

- Track multiple products and target prices.
- Automatically fetch current prices from e-commerce sites.
- Store price history in a local SQLite database.
- Analyse trends (min/max/avg, up/down/stable).
- Send email alerts when price drops below or equals the target.

### Technologies

- Python 3.10 or above
- Libraries:
  - `requests`, `beautifulsoup4`, `schedule`
  - Standard library: `smtplib`, `time`, `sqlite3`
- Optional (for price trend analysis and visualisation):
  - `matplotlib` (for plotting price history)

### Installation

1. (Optional) Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`

### Running the CLI

From the project root:

```bash
python -m price_tracker.main
```

The menu provides:

1. Add a product (URL + target price)
2. List all tracked products
3. View price history for a product (recent records, min/max/avg, trend)
4. Toggle product active/inactive
5. Start automatic price monitoring (scheduler loop)
6. Exit

### End-to-end demo run

For a quick walkthrough that creates sample products and runs a single
scrape + analyse + (optional) notify cycle:

```bash
python -m price_tracker.demo
```

This script:

- Initializes the database.
- Adds 1–2 sample products.
- Fetches their current prices.
- Stores a snapshot and prints previous vs new price.
- Shows whether an email notification is (or would be) sent.

### Automatic periodic checks (scheduler)

1. Configure SMTP and recipient details via environment variables, e.g.:

   - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SENDER_EMAIL`
   - `ALERT_RECIPIENT_EMAIL` (address to receive alerts)

2. Run the CLI and choose menu option **5**:

   - The scheduler will:
     - load active products,
     - scrape current prices,
     - store price history,
     - compare with target price,
     - send email alerts when `current_price <= target_price`.
   - The loop continues until you press **Ctrl+C**.

### Viewing price history and trends

From the CLI main menu, choose option **3**:

- Select a product by ID.
- View recent price records (timestamp + price).
- See min, max, and average price over history.
- See a simple trend indicator: "up", "down", or "stable".

Optionally, you can call `export_price_history_plot` from code to save a
PNG line chart if `matplotlib` is installed.

### Basic tests

Simple smoke tests are provided in `tests_basic.py` and can be run from
the project root with:

```bash
python tests_basic.py
```

These tests exercise:

- price analyzer logic,
- generic scraper parser using mocked HTML,
- storage round-trip for products and price history.

### Limitations and future enhancements

- The notifier currently sends email; `send_sms_notification` and
  `send_push_notification` are provided as stubs for future SMS/desktop
  integration.
- The scraper includes basic support for Amazon and Flipkart plus a
  generic parser; additional site-specific parsers can be added by
  extending `scraper.py`.
- Potential future extensions include:
  - multi-site comparison dashboards,
  - a browser extension for easier URL capture,
  - a GUI or web interface for configuration and history visualisation.