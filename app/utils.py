from bs4 import Tag

from app.items import Product


def get_single_laptop(laptop: Tag) -> Product:
    return Product(
        title=laptop.select_one("a.title")["title"],
        description=laptop.select_one(
            "p.card-text.description"
        ).text.replace(
            "\xa0",
            " "
        ),
        price=convert_str_price(laptop),
        rating=get_product_rating(laptop),
        num_of_reviews=get_num_of_reviews(laptop)
    )


def get_single_tablet(tablet: Tag) -> Product:
    return Product(
        title=tablet.select_one("a.title")["title"],
        description=tablet.select_one(
            "p.card-text.description"
        ).text.replace(
            "\xa0",
            " "
        ),
        price=convert_str_price(tablet),
        rating=get_product_rating(tablet),
        num_of_reviews=get_num_of_reviews(tablet)
    )


def get_single_touch(touch: Tag) -> Product:
    return Product(
        title=touch.select_one("a.title")["title"],
        description=touch.select_one(
            "p.card-text.description"
        ).text.replace(
            "\xa0",
            " "
        ),
        price=convert_str_price(touch),
        rating=get_product_rating(touch),
        num_of_reviews=get_num_of_reviews(touch)
    )


async def get_single_phone(phone: Tag) -> Product:
    return Product(
        title=phone.select_one("a.title")["title"],
        description=phone.select_one(
            "p.card-text.description"
        ).text.replace(
            "\xa0",
            " "
        ),
        price=convert_str_price(phone),
        rating=get_product_rating(phone),
        num_of_reviews=get_num_of_reviews(phone)
    )


async def parse_single_home_product(product: Tag) -> Product:
    return Product(
        title=product.select_one("a.title")["title"],
        description=product.select_one(
            "p.card-text.description"
        ).text.replace(
            "\xa0",
            " "
        ),
        price=convert_str_price(product),
        rating=get_product_rating(product),
        num_of_reviews=get_num_of_reviews(product)
    )


async def parse_single_computer(computer: Tag) -> Product:
    return Product(
        title=computer.select_one("a.title")["title"],
        description=computer.select_one(
            "p.card-text.description"
        ).text.replace(
            "\xa0",
            " "
        ),
        price=convert_str_price(computer),
        rating=get_product_rating(computer),
        num_of_reviews=get_num_of_reviews(computer)
    )


def convert_str_price(selector: Tag) -> float:
    return float(selector.select_one("h4.price").text.replace("$", ""))


def get_product_rating(selector: Tag) -> int:
    return len(selector.select("span.ws-icon"))


def get_num_of_reviews(selector: Tag) -> int:
    return int(selector.select_one("p.review-count").text.split()[0])
