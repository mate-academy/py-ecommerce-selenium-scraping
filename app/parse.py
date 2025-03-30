import time
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException, WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.select import Select


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers")
LAPTOPS_URL = urljoin(HOME_URL, "computers/laptops")
TABLETS_URL = urljoin(HOME_URL, "computers/tablets")
PHONES_URL = urljoin(HOME_URL, "phones")
TOUCH_URL = urljoin(HOME_URL, "phones/touch")


@dataclass
class ProductDTO:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_all_products() -> None:
    pass


def get_driver(headless: bool = False) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    options.add_argument("-profile")
    options.add_argument("--user-data-dir=/home/user/.config/google-chrome")

    return webdriver.Chrome(options=options)


def get_product_detail(
        driver: webdriver.Chrome,
        product_links: list
) -> list[ProductDTO]:
    product_data: list[ProductDTO] = []

    for link in product_links:
        driver.get(link)
        wait = WebDriverWait(driver, timeout=10)
        try:
            print(link)
            product_name = wait.until(
                ec.presence_of_element_located(
                    (By.CSS_SELECTOR, "h4.title.card-title")
                )
            ).text.strip()
            print(product_name)
            product_description = driver.find_element(
                By.CSS_SELECTOR, "p.description.card-text"
            ).text.strip()
            print(product_description)
            product_num_of_reviews = int(
                driver.find_element(By.CSS_SELECTOR, "p.review-count")
                .text.strip()
                .split()[0]
            )
            print(product_num_of_reviews)
            product_rating = len(
                driver.find_elements(
                    By.CSS_SELECTOR,
                    "span.ws-icon.ws-icon-star"
                )
            )
            print(product_rating)

            try:
                hdd_buttons = driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.swatches button.swatch"
                )

                product_prices = {}
                for button in hdd_buttons:
                    hdd_size = button.get_attribute("value")
                    driver.execute_script(
                        "arguments[0].click();",
                        button
                    )
                    time.sleep(0.1)
                    price = round(
                        float(
                            wait.until(
                                ec.presence_of_element_located(
                                    (By.CSS_SELECTOR, "h4.price")
                                )
                            )
                            .text.strip()
                            .replace("$", "")
                        ),
                        2
                    )
                    product_prices[hdd_size] = price
            except NoSuchElementException as e:
                product_prices = {}
            print(product_prices)

            try:
                color_dropdown = driver.find_element(
                    By.CSS_SELECTOR, "select[aria-label='color']"
                )
                color_options = color_dropdown.find_elements(
                    By.TAG_NAME, "option"
                )
                color_values = []
                for color_option in color_options:
                    color_value = color_option.get_attribute("value")
                    if color_value:
                        try:
                            Select(color_dropdown).select_by_value(color_value)
                            time.sleep(1)
                        except NoSuchElementException as e:
                            print(e)

            except NoSuchElementException as e:
                pass

        except (TimeoutException, NoSuchElementException) as e:
            print(e)
    return product_data


def main(url: str, headless: bool = False) -> None:
    driver = get_driver(headless)
    scroll_and_load_all_products(driver, url)
    links = get_all_products_links(driver)
    get_product_detail(driver, links)
    print(len(links))
    driver.quit()


def scroll_and_load_all_products(driver: webdriver.Chrome, url: str) -> None:
    driver.get(url)
    wait = WebDriverWait(driver=driver, timeout=2)
    try:
        cookie_button = wait.until(
            ec.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.acceptCookies")
            )
        )
        cookie_button.click()
        time.sleep(0.1)
    except (TimeoutException, NoSuchElementException):
        pass

    while True:
        try:
            more_button = wait.until(
                ec.presence_of_element_located(
                    (By.CSS_SELECTOR, "a.ecommerce-items-scroll-more")
                )
            )
            driver.execute_script(
                "arguments[0].scrollIntoView();",
                more_button
            )
            time.sleep(0.1)
            more_button.click()
            time.sleep(0.1)

        except WebDriverException as e:
            print(str(e))
            break
    return None


def get_all_products_links(driver: webdriver.Chrome):
    products_links = []

    try:
        WebDriverWait(driver=driver, timeout=1).until(
            ec.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.card.thumbnail")
            )
        )
        product_elements = driver.find_elements(
            By.CSS_SELECTOR,
            "div.card.thumbnail a.title"
        )
        for element in product_elements:
            product_link = element.get_attribute("href")
            if product_link:
                products_links.append(product_link)
    except (TimeoutException, NoSuchElementException) as e:
        print(e)
        pass

    return products_links


if __name__ == "__main__":
    main(headless=False, url=TOUCH_URL)
