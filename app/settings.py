BASE_URL = "https://webscraper.io"

lst_paths = [
    "test-sites/e-commerce/more/",
    "test-sites/e-commerce/more/computers/",
    "test-sites/e-commerce/more/computers/laptops",
    "test-sites/e-commerce/more/computers/tablets",
    "test-sites/e-commerce/more/phones/",
    "test-sites/e-commerce/more/phones/touch",
]

lst_urls = [f"{BASE_URL}/{path}" for path in lst_paths]
