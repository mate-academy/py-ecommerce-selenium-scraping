import csv
from tqdm import tqdm
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        button = WebDriverWait(driver, 5).until(
            ec.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[data-tid='banner-accept']")
            )
        )
        button.click()
    except TimeoutException:
        pass


def accept_more(driver: webdriver.Chrome) -> None:
    while True:
        buttons = driver.find_elements(
            By.CSS_SELECTOR, "a.ecomerce-items-scroll-more")

        # кнопки немає або вона вже прихована — всі товари завантажені
        if not buttons or not buttons[0].is_displayed():
            break

        old_count = len(driver.find_elements(By.CLASS_NAME, "card-body"))

        driver.execute_script("arguments[0].click();", buttons[0])

        try:
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(
                    By.CLASS_NAME, "card-body")) > old_count
            )
        except TimeoutException:
            break


def parse_single_product(card: WebElement) -> Product:

    return Product(
        title=card.find_element(
            By.CLASS_NAME,
            "title").get_attribute("title"),
        description=card.find_element(By.CLASS_NAME, "description").text,
        price=float(card.find_element(
            By.CLASS_NAME,
            "price").text.replace("$", "")),
        rating=len(card.find_elements(By.CSS_SELECTOR, ".ws-icon-star")),
        num_of_reviews=int(
            card.find_element(
                By.CSS_SELECTOR,
                "span[itemprop='reviewCount']").text
        ),
    )


def write_products_to_csv(products: list[Product], file_name: str) -> None:
    file_name += ".csv"

    with open(file_name, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_subcategory_data(driver: webdriver.Chrome,
                         category_url: str) -> dict[str, str]:
    driver.get(category_url)
    links = driver.find_elements(By.CSS_SELECTOR, "a.subcategory-link")
    return {
        link.get_attribute("textContent").strip().lower():
            link.get_attribute("href")
        for link in links
    }


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(HOME_URL)
        accept_cookies(driver)

        # ЕТАП 1: збираємо словник {ім'я файлу: посилання}
        urls = driver.find_elements(By.CSS_SELECTOR, "a[itemprop='url']")
        names = driver.find_elements(By.CSS_SELECTOR, "span[itemprop='name']")

        product_dict = {"home": HOME_URL}
        product_dict.update(
            {
                name.get_attribute("textContent")
                .strip()
                .lower(): url.get_attribute("href")
                for name, url in zip(names, urls)
            }
        )

        # заходимо в кожну категорію і додаємо її підкатегорії
        for page_url in list(product_dict.values()):
            product_dict.update(get_subcategory_data(driver, page_url))

        print(product_dict)

        # ЕТАП 2: ітеруємося по словнику, парсимо і пишемо у файли
        for file_name, page_url in tqdm(product_dict.items(), desc="Сторінки"):
            driver.get(page_url)
            accept_more(driver)

            cards = driver.find_elements(By.CLASS_NAME, "thumbnail")
            products = [
                parse_single_product(card)
                for card in tqdm(cards, desc=file_name, leave=False)
            ]

            write_products_to_csv(products, file_name)
            tqdm.write(f"{file_name}.csv: {len(products)} товарів")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
