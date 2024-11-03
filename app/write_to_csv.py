import csv
from typing import List
from dataclasses import asdict

from app.product import Product


def write_to_csv(file_name: str, products: List[Product]) -> None:
    product_fields = [
        field.name for field in Product.__dataclass_fields__.values()
    ]
    with open(file_name, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(product_fields)
        writer.writerows([asdict(product).values() for product in products])
