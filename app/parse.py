from time import sleep

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
    cookies_button = wait.until(expected_conditions.element_to_be_clickable(cookies_button_locator))

    cookies_button.click()


def get_inner_urls(links: list, driver: webdriver) -> list:
    inner_links = []

    for link in links:
        driver.get(link)
        inner_mix = driver.find_elements(By.CSS_SELECTOR, config.CLASS_INNER_URLS)

        for inner_link in inner_mix:
            inner_links.append(inner_link.get_attribute("href"))

    return inner_links


def click_button_more(driver: webdriver, link: str):

    try:
        driver.get(link)
        more_button = driver.find_elements(By.CLASS_NAME, config.CLASS_MORE_BUTTON)[0]
        while more_button.is_displayed():
            sleep(0.3)
            more_button = driver.find_elements(By.CLASS_NAME, config.CLASS_MORE_BUTTON)[0]
            more_button.click()
    except (TimeoutException, ElementNotInteractableException):
        return


def get_info_from_product(driver:webdriver, links: str) -> list[config.Product]:
    for link in links:
        driver.get(link)
        click_button_more(driver, link)
        products = driver.find_elements(By.CLASS_NAME, config.CLASS_PRODUCT)


def get_all_products() -> None:
    options = Options()
    options.add_argument(config.CHROME_OPTIONS)

    driver = webdriver.Chrome()
    driver.get(config.HOME_URL)

    click_on_cookies(driver=driver)

    links = driver.find_elements(By.CSS_SELECTOR, ".sidebar-nav > ul > li > a")
    # print(links[2].get_attribute("href"))
    # links[2].click()
    all_links = []

    for link in links:
        all_links.append(link.get_attribute("href"))

    all_links.extend(get_inner_urls(all_links, driver))

    # click_button_more(driver, "https://webscraper.io/test-sites/e-commerce/more/computers/laptops")

    products = driver.find_elements(By.CLASS_NAME, config.CLASS_PRODUCT)
    for product in products:
        p = Product
        print(type(p))
        p.title = product.find_element(By.CLASS_NAME, config.CLASS_TITLE).get_attribute(config.CLASS_TITLE)
        p.description = product.find_element(By.CLASS_NAME, config.CLASS_DESCRIPTION).text
        price = product.find_element(By.CLASS_NAME, config.CLASS_PRICE).text
        price = float(price.replace("$", ""))
        p.price = price
        p.rating = 5
        p.num_of_reviews = 1

    print(p.__str__(p))

    print(all_links)




    driver.close()


if __name__ == "__main__":
    get_all_products()
