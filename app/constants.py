from urllib.parse import urljoin


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(
    BASE_URL,
    "test-sites/e-commerce/more/computers/laptops"
)
TABLETS_URL = urljoin(
    BASE_URL,
    "test-sites/e-commerce/more/computers/tablets"
)
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

URLS = {
    HOME_URL: "home.csv",
    COMPUTERS_URL: "computers.csv",
    LAPTOPS_URL: "laptops.csv",
    TABLETS_URL: "tablets.csv",
    PHONES_URL: "phones.csv",
    TOUCH_URL: "touch.csv",
}
