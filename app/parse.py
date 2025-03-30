from urllib.parse import urljoin
import time
import csv

from selenium.common import NoSuchElementException, TimeoutException
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

class Product:
    def __init__(self, title, description, price, rating, num_of_reviews):
        self.title = title
        self.description = description
        self.price = price
        self.rating = rating
        self.num_of_reviews = num_of_reviews

    def to_csv_row(self):
        return [self.title, self.description, self.price, self.rating, self.num_of_reviews]


def create_driver():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    return driver


def get_ratings_count(ratings_container):
    try:
        paragraphs = ratings_container.find_elements(By.TAG_NAME, "p")

        if len(paragraphs) >= 2:
            second_paragraph = paragraphs[1]
            spans = second_paragraph.find_elements(By.TAG_NAME, "span")
            return len(spans)
        else:
            return 0
    except Exception as e:
        print(f"Error in counting <span> in the second paragraph: {e}")
        return 0


def get_review_count(ratings_container):
    try:
        first_rating_elem = ratings_container.find_element(By.TAG_NAME, "p")
        review_text = first_rating_elem.text.split(" ")
        return review_text[0] if review_text else 0
    except Exception as e:
        print(f"Error retrieving the text of the first paragraph in the .ratings container: {e}")
        return 0


def close_cookie_banner(driver):
    try:
        cookie_banner = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.ID, "cookieBanner"))
        )
        close_button = cookie_banner.find_element(By.XPATH, './/button[contains(text(), "Accept")]')
        close_button.click()
        print("The cookies banner is closed.")
    except Exception as e:
        print(f"Failed to close the cookie banner")


def click_more_until_disappear(driver, max_retries=3):
    close_cookie_banner(driver)
    attempts = 0

    while attempts < max_retries:
        try:
            more_link = WebDriverWait(driver, 1).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".ecomerce-items-scroll-more"))
            )
            print(f"Attempt {attempts + 1}: Clicking 'More'.")

            driver.execute_script("arguments[0].scrollIntoView(true);", more_link)
            driver.execute_script("arguments[0].click();", more_link)
            print("Clicking on the 'More' link is done.")
            attempts = 0
            time.sleep(1)

            status = WebDriverWait(driver, 1).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".ecomerce-items-scroll-more"))
            )
            if status:
                print(f"The 'More' link has disappeared.")
                break

        except TimeoutException as e:
            attempts += 1
            print(f"Attempt {attempts}: Error when clicking on the 'More' link")
            if attempts >= max_retries:
                print("Max retries reached. Exiting.")
                break  # Exit the loop after reaching the maximum retries


def scrape_page(driver, url, csv_file_name):
    driver.get(url)

    products = []

    click_more_until_disappear(driver)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".thumbnail"))
        )
    except:
        print("Product elements not found.")

    product_elements = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")

    for product_elem in product_elements:
        title = product_elem.find_element(By.CSS_SELECTOR, ".title").get_attribute("title")
        description = product_elem.find_element(By.CSS_SELECTOR, ".description").text
        price = float(product_elem.find_element(By.CSS_SELECTOR, ".price").text.strip("$"))

        try:
            ratings_and_reviews_container = product_elem.find_element(By.CSS_SELECTOR, ".ratings")
            rating_count = get_ratings_count(ratings_and_reviews_container)
            num_of_reviews = get_review_count(ratings_and_reviews_container)
        except NoSuchElementException:
            rating_count = 0
            num_of_reviews = 0


        product = Product(title, description, price, rating_count, num_of_reviews)
        products.append(product)

    with open(csv_file_name, mode="w", newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])
        for product in products:
            writer.writerow(product.to_csv_row())
    print(f"Data saved to {csv_file_name}")


def get_all_products() -> None:
    driver = create_driver()

    pages = [
        (HOME_URL, "home.csv"),
        (urljoin(BASE_URL, "test-sites/e-commerce/more/computers"), "computers.csv"),
        (urljoin(BASE_URL, "test-sites/e-commerce/more/phones"), "phones.csv"),
        (urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"), "laptops.csv"),
        (urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"), "tablets.csv"),
        (urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"), "touch.csv")
    ]

    for url, csv_file_name in tqdm(pages, desc="Scraping Pages"):
        scrape_page(driver, url, csv_file_name)

    driver.quit()


if __name__ == "__main__":
    get_all_products()