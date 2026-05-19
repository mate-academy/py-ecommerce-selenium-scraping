from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from app.config.parser_config import Product


def scrape_single_product(product: WebElement, driver: WebDriver) -> Product:
    ActionChains(driver).scroll_to_element(product).perform()
    price = product.find_element(By.CLASS_NAME, "price")
    price_float = float(price.text.replace("$", ""))
    title = product.find_element(By.CLASS_NAME, "title").get_attribute("title")
    description = product.find_element(By.CLASS_NAME, "description").text
    rating = len(product.find_elements(By.CSS_SELECTOR, ".ratings .ws-icon"))
    num_of_reviews_driver = product.find_element(
        By.CSS_SELECTOR, ".ratings"
    ).text
    num_of_reviews = int(num_of_reviews_driver.split()[0])

    product_model = Product(
        title=title,
        description=description,
        price=price_float,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )
    return product_model
