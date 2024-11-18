from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


def get_dynamic_content(url: str) -> str:
    """Fetch dynamic content for pages requiring JavaScript interaction."""
    options = Options()
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    clicks_left = 20

    while clicks_left:
        try:
            load_more_link = WebDriverWait(driver, 5).until(
                ec.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
            driver.execute_script(
                "arguments[0].scrollIntoView(true);",
                load_more_link
            )
            load_more_link.click()
            time.sleep(3)
        except TimeoutException:
            print("Timed out waiting for the 'Load More' link.")
            break
        except NoSuchElementException:
            print("No 'Load More' link found.")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

    html = driver.page_source
    driver.quit()
    return html
