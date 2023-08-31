import csv
from time import sleep

from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm

from selenium.common import TimeoutException, ElementNotInteractableException

from app import config
from selenium import webdriver

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions

from app.config import Product


def click_on_cookies(driver: webdriver) -> None:
    wait = WebDriverWait(driver, 10)
    cookies_button_locator = (By.CLASS_NAME, config.CLASS_BUTTON_COOKIES)
    cookies_button = wait.until(
        expected_conditions.element_to_be_clickable(cookies_button_locator))

    cookies_button.click()


def click_button_more(driver: webdriver, link: str) -> None:

    try:
        driver.get(link)
        more_button = driver.find_elements(
            By.CLASS_NAME,
            config.CLASS_MORE_BUTTON
        )[0]
        while more_button.is_displayed():
            sleep(0.3)
            more_button = driver.find_elements(
                By.CLASS_NAME,
                config.CLASS_MORE_BUTTON
            )[0]
            more_button.click()
    except (TimeoutException, ElementNotInteractableException, IndexError):
        return


def get_one_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(
            By.CLASS_NAME,
            config.CLASS_TITLE
        ).get_attribute(config.CLASS_TITLE),
        description=product.find_element(
            By.CLASS_NAME,
            config.CLASS_DESCRIPTION
        ).text,
        price=float(product.find_element(
            By.CLASS_NAME,
            config.CLASS_PRICE
        ).text.replace("$", "")),
        rating=len(product.find_elements(
            By.CLASS_NAME,
            config.CLASS_STAR_RATING
        )),
        num_of_reviews=int(product.find_element(
            By.CSS_SELECTOR,
            config.CLASS_REVIEW
        ).text.split()[0]),
    )


def get_inner_urls(links: list, driver: webdriver) -> list:
    inner_links = []

    for link in links:
        driver.get(link)
        inner_mix = driver.find_elements(
            By.CSS_SELECTOR,
            config.CLASS_INNER_URLS
        )

        for inner_link in inner_mix:
            inner_links.append(inner_link.get_attribute("href"))

    return inner_links


def write_to_file(file_name: str, product_list: list) -> None:
    with open(file_name, "w", encoding="utf-8", newline="") as products_file:
        writer = csv.DictWriter(
            products_file,
            fieldnames=config.PRODUCT_FIELDS
        )
        writer.writeheader()
        for product in product_list:
            writer.writerow(product.__dict__)


def get_info_from_product(driver: webdriver, links: list) -> None:
    for link in tqdm(links):
        driver.get(link)
        click_button_more(driver, link)
        products = driver.find_elements(By.CLASS_NAME, config.CLASS_PRODUCT)
        product_list = [get_one_product(product) for product in products]
        file_name = link.split("/")[-1] + ".csv"
        write_to_file(file_name, product_list)


def get_all_products() -> None:
    options = Options()
    options.add_argument(config.CHROME_OPTIONS)

    driver = webdriver.Chrome(options=options)
    driver.get(config.HOME_URL)

    click_on_cookies(driver=driver)

    links = driver.find_elements(By.CSS_SELECTOR, config.CLASS_URLS)

    all_links = []

    for link in tqdm(links):
        all_links.append(link.get_attribute("href"))

    all_links.extend(get_inner_urls(all_links, driver))

    get_info_from_product(driver, all_links)

    driver.close()


if __name__ == "__main__":
    get_all_products()
