import scrapy
from scrapy.http import Response

from app.parse import Product
from helpers import parse_single_product


class PhonesSpider(scrapy.Spider):
    name = "phones"
    allowed_domains = ["webscraper.io"]
    start_urls = ["https://webscraper.io/test-sites/e-commerce/more/phones"]

    def parse(self, response: Response, **kwargs) -> Product:
        for product in response.css(".thumbnail"):
            yield parse_single_product(product)
