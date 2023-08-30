import requests
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup, Tag
from app import config


options = Options()
options.add_argument("")

driver = webdriver.Chrome(options=options)
driver.get(config.BASE_URL)



# page = requests.get(config.BASE_URL).content
# soup = BeautifulSoup(page, config.HTML_PARSER)


def get_single_product(product_driver: webdriver) -> config.Product:
    return [product_driver.find_element(By.CSS_SELECTOR, )


def get_all_products_from_page(driver: webdriver) -> list:

    links_list = get_all_links(driver)

    products = soup.select(config.CLASS_PRODUCT)
    return [get_single_product(product_soup) for product_soup in products]

driver.find_element(By.CSS_SELECTOR)

