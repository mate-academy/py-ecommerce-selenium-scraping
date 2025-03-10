from collections import defaultdict
import csv
from dataclasses import astuple, dataclass, fields
from typing import Generator
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import ElementClickInterceptedException
from bs4 import BeautifulSoup, Tag
import requests
from tqdm import tqdm
import cProfile
import pstats
from line_profiler import LineProfiler

call_counts = defaultdict(int)

def profile_function(func):
    def wrapper(*args, **kwargs):
        global call_counts
        call_counts[func.__name__] += 1  # Increment call count

        profiler = LineProfiler()
        profiler.add_function(func)
        profiler.enable()
        
        result = func(*args, **kwargs)
        
        profiler.disable()
        
        # Generate unique filename: function_name{call_number}.txt
        file_name = f"{func.__name__}_{call_counts[func.__name__]}.txt"
        with open(file_name, "w") as f:
            profiler.print_stats(stream=f)
        
        print(f"Profiling results saved to {file_name}")
        return result
    return wrapper

class RequestCounter:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.request_count = 0

    def get(self, url: str, timeout: int = 5) -> requests.Response:
        self.request_count += 1
        print(f"Request #{self.request_count} → {url}")
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def close(self) -> None:
        self.session.close()


counter = RequestCounter()


BASE_URL = "https://webscraper.io/"
# HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
HOME_URL = "test-sites/e-commerce/more/"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    # additional_info: dict


PRODUCT_FIELDS = [field.name for field in fields(Product)]

@profile_function
def get_pages_links(
    base_url: str, page_link: str, pages_links: set[str] = None
) -> Generator[tuple[str, str], None, None]:
    if pages_links is None:
        pages_links = set()

    try:
        response = counter.get(urljoin(base_url, page_link), timeout=5)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return

    main_page_soup = BeautifulSoup(response.text, "html.parser")
    main_content = main_page_soup.select_one(".sidebar-nav")
    if not main_content:
        return

    links = main_content.select(".nav-link")
    for link in links:
        page_url = link.get("href")
        page_name = link.get_text().strip()

        if (
            page_url
            and link.get("aria-label") == "Navigation category"
            and page_url not in pages_links
        ):
            pages_links.add(page_url)
            yield page_url, page_name
            yield from get_pages_links(base_url, page_url, pages_links)
        elif page_url and page_url not in pages_links:
            pages_links.add(page_url)
            yield page_url, page_name


@profile_function
def remove_overlay(driver: webdriver) -> None:
    try:
        cookie_banner = WebDriverWait(driver, timeout=1).until(
            ec.presence_of_element_located((By.ID, "cookieBanner"))
        )
        close_button = cookie_banner.find_element(
            By.CLASS_NAME, "acceptCookies"
        )
        close_button.click()
    except Exception:
        # print(f"Exception occurred while handling cookie banner: {e}")
        pass

@profile_function
def expand_page(driver: webdriver, page_url: str) -> None:
    absolute_url = urljoin(BASE_URL, page_url)
    driver.get(absolute_url)
    wait = WebDriverWait(driver, 10)
    remove_overlay(driver)
    while True:
        try:

            load_more_btn = wait.until(
                ec.element_to_be_clickable(
                    (By.XPATH, "//a[contains(text(), 'More')]")
                )
            )

            load_more_btn.click()
            print("Clicked Load More button")

        except Exception:
            # print(f"Error: {e}")
            # print("No more 'Load More' button found or all content loaded.")
            break

    elements = driver.find_elements(By.CLASS_NAME, "card-body")
    print(f"Found {len(elements)} elements")
    expanded_page_soup = BeautifulSoup(driver.page_source, "html.parser")
    return expanded_page_soup


def parse_hdd_block_prices(product_soup: Tag) -> dict[str, float]:
    absolute_url = urljoin(BASE_URL, product_soup.select_one(".title")["href"])
    # hdd_block = product_soup.select_one(".hdd")
    driver = webdriver.Chrome()
    driver.get(absolute_url)
    swatches = driver.find_element(By.CLASS_NAME, "swatches")
    buttons = swatches.find_elements(By.TAG_NAME, "button")
    prices = {}
    remove_overlay(driver)
    for button in buttons:
        if not button.get_property("disabled"):
            try:
                button.click()
            except ElementClickInterceptedException:
                print("Element click intercepted.")

            prices[button.get_property("value")] = float(
                driver.find_element(By.CLASS_NAME, "price")
                .text.replace("$", "")
            )
    return prices


def parse_single_product(product: Tag) -> Product:
    # hdd_prices  = parse_hdd_block_prices(product)
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").get_text(),
        price=float(product.select_one(".price").get_text().replace("$", "")),
        rating=len(product.select(".ws-icon-star")),
        num_of_reviews=int(
            product.select_one(".review-count").get_text().split()[0]
        ),
        # additional_info={"hdd_prices": hdd_prices},
    )


def get_products(expanded_page_soup: BeautifulSoup) -> list[Product]:
    products = expanded_page_soup.select(".card-body")
    return [
        parse_single_product(product)
        for product in tqdm(products, desc="Parsing products")
    ]


def write_products_to_csv(
    products: list[Product], filename: str = "results.csv"
) -> None:
    with open(f"{filename}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)

    pages_links = get_pages_links(BASE_URL, HOME_URL)
    for page_url, page_name in pages_links:
        expanded_page_soup = expand_page(driver, page_url)
        products = get_products(expanded_page_soup)
        write_products_to_csv(products, page_name)

    print("done")
    counter.close()
    driver.quit()


if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()
    get_all_products()
    profiler.disable()
    profiler.dump_stats("profile_output.prof")

    stats = pstats.Stats("profile_output.prof").sort_stats("tottime")
    stats.print_stats(10)
