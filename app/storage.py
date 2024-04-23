import csv
from dataclasses import dataclass, fields, astuple


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def csv_writer(filename: str, products: list[Product]) -> None:
    with open(f"{filename}.csv", "w+") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])

