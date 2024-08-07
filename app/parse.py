import time
import csv
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from app.settings import URLS, Product
from app.web_driver import WebDriver


def parse_product(product_element):
    try:
        title = product_element.find_element(
            By.CLASS_NAME, "title"
        ).get_property("title")
        description = product_element.find_element(
            By.CLASS_NAME, "description"
        ).text.strip()
        price = float(product_element.find_element(
            By.CLASS_NAME, "price"
        ).text.replace("$", ""))
        rating = len(product_element.find_elements(
            By.CLASS_NAME, "ws-icon-star"
        ))
        if not rating:
            rating = 0
            print("\t('rating' set to 0 because of error)")

        review_elements = product_element.find_elements(
            By.CLASS_NAME, "review-count"
        )
        if review_elements:
            num_of_reviews = int(
                review_elements[0].text.replace(" reviews", "")
            )
        else:
            num_of_reviews = 0
            print("\t('num_of_reviews' set to 0 because of error)")

        return Product(title, description, price, rating, num_of_reviews)

    except Exception as e:
        print(f"Error parsing product: {e}")
        return None


def parse_process(driver, url):
    print(f"\nAccessing {url}")
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "caption"))
    )

    product_elements = driver.find_elements(By.CLASS_NAME, "caption")

    products = []
    for index, product_element in enumerate(product_elements, 1):
        print(f"\tParsing product {index}/{len(product_elements)}...")
        product = parse_product(product_element)
        if product:
            products.append(product)

    return products


def write_to_csv(file_name, products):
    fieldnames = ["title", "description", "price", "rating", "num_of_reviews"]

    with open(file_name, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(fieldnames)
        print(f"\nWriting data to {file_name}.csv file...")

        for product in products:
            writer.writerow([getattr(product, field) for field in fieldnames])

        print(f"Writing data to {file_name}.csv file finished!")
        print("-" * 70)


def get_all_products():
    print("\n======= Ecommerce Selenium Scraping =======")

    start_counter = time.perf_counter()

    with WebDriver() as web_driver:
        driver = web_driver.get_driver()

        pages = {
            "home": URLS["HOME_PAGE_URL"],
            "computers": URLS["COMPUTERS_PAGE_URL"],
            "laptops": URLS["LAPTOPS_PAGE_URL"],
            "tablets": URLS["TABLETS_PAGE_URL"],
            "phones": URLS["PHONES_PAGE_URL"],
            "touch": URLS["TOUCH_PAGE_URL"]
        }

        for page_name, url in pages.items():
            print(f"\nParsing page with '{page_name}' products...")
            products = parse_process(driver, url)
            print(f"\nParsing page with '{page_name}' products finished!")
            write_to_csv(f"{page_name}.csv", products)

    end_counter = time.perf_counter()
    print("Scraping completed.")
    print(f"Spent time: {end_counter - start_counter}")


if __name__ == "__main__":
    get_all_products()
