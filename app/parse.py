import csv
from dataclasses import dataclass, fields, astuple
# from datetime import time
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException
)
import time

from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(LAPTOPS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")

URL_LIST = [
    {"name": "home", "url": HOME_URL},
    {"name": "computers", "url": COMPUTERS_URL},
    {"name": "laptops", "url": LAPTOPS_URL},
    {"name": "tablets", "url": TABLETS_URL},
    {"name": "phones", "url": PHONES_URL},
    {"name": "touch", "url": TOUCH_URL},
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def start_driver() -> WebDriver:
    service = ChromeService(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def write_products_to_csv(products: list[Product], name: str = "results") -> None:
    with open(f"{name}.csv", "w") as f:
        print(f"Створюю {name}.csv")
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])
        print(f"{name}.csv створено")


def parse_single_product(product: WebElement) -> Product:
    title = product.find_element(By.CLASS_NAME, "title").get_attribute("title")
    price = float(
        product.find_element(
            By.CLASS_NAME, "price"
        ).text.strip().replace("$", ""))
    description = product.find_element(
        By.CLASS_NAME, "description").text.strip()
    rating = len(product.find_elements(By.CLASS_NAME, "ws-icon-star"))
    num_of_reviews = int(
        product.find_element(By.CLASS_NAME, "review-count").text.split()[0]
    )
    print(dict(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    ))

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def get_products_via_selenium(url: str) -> list[Product] | None:
    driver = start_driver()
    wait = WebDriverWait(driver, 10)
    try:
        print("Завантажую сторінку...")
        driver.get(url)
        print("Сторінка завантажена.")
        try:
            more_button_candidate = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            driver.execute_script(
                "arguments[0].scrollIntoView(true);", more_button_candidate
            )
            print("Проскролили до кнопки 'More'.")
            time.sleep(0.5)  # Дати сторінці час на перемалювання після скролу
        except NoSuchElementException:
            print("Кнопка 'More' не знайдена.")
            # Якщо кнопки взагалі немає, значить, тут немає пагінації з "More"
            # return products_list  # Повертаємо пустий список

        # --- Крок 2: Цикл пагінації ---
        while True:
            try:
                current_product_count = len(
                    driver.find_elements(By.CLASS_NAME, "col-md-4")
                )
                print(f"Поточна кількість товарів: {current_product_count}")

                button = wait.until(
                    ec.element_to_be_clickable((
                        By.CLASS_NAME, "ecomerce-items-scroll-more"
                    ))
                )
                print("Кнопка 'More' клікабельна. Натискаю...")

                driver.execute_script("arguments[0].click();", button)
                print("Кнопка 'More' клікнута.")

                wait.until(
                    lambda d: len(
                        d.find_elements(By.CLASS_NAME, "col-md-4")
                    ) > current_product_count
                )
                print("Нові товари завантажено. Продовжую пагінацію.")
                time.sleep(0.5)

            except TimeoutException:
                print("Кнопка 'More' більше не клікабельна або "
                      "нові товари не завантажуються. Пагінація завершена.")
                break
            except ElementClickInterceptedException as e:
                print(f"Помилка ElementClickInterceptedException: {e}. "
                      f"Зупиняю пагінацію.")
                break
            except StaleElementReferenceException:
                # Хоча ми заново знаходимо елемент, рідко може виникнути.
                # Просто продовжимо цикл, щоб спробувати знову знайти кнопку.
                print("Виникла StaleElementReferenceException. "
                      "Спробую знайти кнопку 'More' знову.")
                continue
            except Exception as e:
                print(f"Виникла неочікувана помилка в циклі пагінації: {e}")
                break  # Вихід з циклу в разі інших помилок

        print("Пагінація завершена. Збираю всі товари.")
        # --- Крок 3: Збір всіх завантажених товарів ---
        all_product_elements = driver.find_elements(By.CLASS_NAME, "col-md-4")
        products_list = [
            parse_single_product(product_element)
            for product_element in all_product_elements
        ]

        print(f"Знайдено {len(products_list)} товарів.")
        return products_list

    except Exception as e:
        print(f"Виникла загальна помилка під час виконання: {e}")
        return None
    finally:
        driver.quit()
        print("Браузер закрито.")


def get_all_products() -> None:
    for url in URL_LIST:
        write_products_to_csv(
            get_products_via_selenium(url["url"]),
            url["name"]
        )


if __name__ == "__main__":
    get_all_products()
