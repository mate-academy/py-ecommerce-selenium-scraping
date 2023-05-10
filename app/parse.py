from playwright.async_api import Page
from playwright.sync_api import sync_playwright

from app.product import Product
from app.utils import (
    HOME_URL, accept_cookie, btn_more_click_until_exists,
    convert_info_to_object, get_category_name,
    save_products_to_csv, go_next_category_page
)


def get_products(page: Page) -> list[Product]:
    products_info = page.query_selector_all(".thumbnail")
    products = [
        convert_info_to_object(product_info)
        for product_info in products_info
    ]

    return products


def parse_and_save_products_from_categories(page: Page) -> None:
    btn_more_click_until_exists(page)
    products = get_products(page)
    category_name = get_category_name(page)

    save_products_to_csv(products, category_name)
    is_stop_program = go_next_category_page(page)
    if is_stop_program:
        return

    parse_and_save_products_from_categories(page)


def get_all_products() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(HOME_URL)
        accept_cookie(page)

        parse_and_save_products_from_categories(page)


if __name__ == "__main__":
    get_all_products()
