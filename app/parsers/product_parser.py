from bs4 import Tag

from app.config import get_settings
from app.models import Product

settings = get_settings()


def parse_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title.card-title").text,
        description=product.select_one(".description.card-text").text,
        rating=len(product.select(".ws-icon.ws-icon-star")),
        num_of_reviews=int(
            product.select_one('span[itemprop="reviewCount"]').text
        ),
        price=float(
            product.select_one("div.caption h4.price").text.replace("$", "")
        ),
    )
