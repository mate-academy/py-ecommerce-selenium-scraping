import csv
from urllib.parse import urljoin

from playwright.async_api import ElementHandle, Page

from app.product import PRODUCT_FIELDS, Product

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


def accept_cookie(page: Page) -> None:
    page.query_selector(".acceptCookies").click()


def btn_more_click_until_exists(page: Page) -> None:
    page.wait_for_timeout(100)
    btn_more = page.query_selector(".ecomerce-items-scroll-more")
    if not btn_more:
        return

    is_visible = "none" not in btn_more.evaluate(
        "element => element.style.display"
    )

    while is_visible:
        btn_more.click()
        page.wait_for_timeout(100)
        is_visible = "none" not in btn_more.evaluate(
            "element => element.style.display"
        )


def get_category_name(page: Page) -> str:
    home_banner = page.query_selector(".jumbotron")
    if home_banner:
        return "home"
    return page.url.split("/")[-1]


def convert_info_to_object(product_info: ElementHandle) -> Product:
    title = product_info.query_selector(".title").get_attribute("title")
    price = float(
        product_info.query_selector(".price")
        .text_content().replace("$", "")
    )

    rating = len(product_info.query_selector_all(".ratings .glyphicon-star"))
    n_reviews = int(
        product_info
        .query_selector(".ratings .pull-right")
        .text_content().split()[0]
    )

    description = (
        product_info
        .query_selector(".description")
        .text_content().replace("\xa0", " ")
    )

    product = Product(
        title=title,
        price=price,
        rating=rating,
        num_of_reviews=n_reviews,
        description=description
    )

    return product


def go_next_category_page(page: Page) -> bool | None:
    """This function allows recursively going through all categories"""

    current_category = page.query_selector("li.active a.active")

    if current_category:
        try:
            next_category = (
                current_category
                .evaluate_handle("element => element.nextElementSibling")
                .query_selector("a")
            )

            next_category.click()
            return

        except AttributeError:
            try:
                next_category = (
                    current_category
                    .evaluate_handle("element => element.parentElement")
                    .evaluate_handle("element => element.nextElementSibling")
                    .query_selector("a")
                )
                if next_category:
                    next_category.click()
                    return
            except AttributeError:
                next_category = page.query_selector("li.active + li")
                if next_category:
                    next_category.click()
                    return
                is_stop = True
                return is_stop

    next_category = page.query_selector("li.active + li")
    if next_category:
        next_category.click()
        return


def save_products_to_csv(products: list[Product], category_name: str) -> None:
    with open(f"{category_name}.csv", mode="w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(PRODUCT_FIELDS)
        for product in products:
            values = list(product.__dict__.values())
            writer.writerow(values)
