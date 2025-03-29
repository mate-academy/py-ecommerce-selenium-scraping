from urllib.parse import urljoin


BASE_URL = "https://webscraper.io/"
HOME = urljoin(BASE_URL, "test-sites/e-commerce/more/")

COMPUTERS = urljoin(HOME, "computers/")
LAPTOPS = urljoin(COMPUTERS, "laptops")
TABLETS = urljoin(COMPUTERS, "tablets")
PHONES = urljoin(HOME, "phones/")
TOUCH = urljoin(PHONES, "touch")


def get_urls() -> dict:
    return {
        HOME: "HOME",
        COMPUTERS: "COMPUTERS",
        LAPTOPS: "LAPTOPS",
        TABLETS: "TABLETS",
        PHONES: "PHONES",
        TOUCH: "TOUCH"
    }
