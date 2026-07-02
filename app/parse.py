import csv
from dataclasses import fields, astuple

from app.models import Product
from app.parse_computers import get_computers_products
from app.parse_home import get_home_products
from app.parse_laptops import get_laptops_products
from app.parse_phones import get_phones_products
from app.parse_tablets import get_tablets_products
from app.parse_touch import get_touch_products

PRODUCT_FIELDS = [field.name for field in fields(Product)]


def write_products_to_csv(
        products: list[Product],
        output_csv_path: str
) -> None:
    with open(output_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    write_products_to_csv(get_home_products(), "home.csv")
    write_products_to_csv(get_computers_products(), "computers.csv")
    write_products_to_csv(get_laptops_products(), "laptops.csv")
    write_products_to_csv(get_tablets_products(), "tablets.csv")
    write_products_to_csv(get_phones_products(), "phones.csv")
    write_products_to_csv(get_touch_products(), "touch.csv")


if __name__ == "__main__":
    get_all_products()
