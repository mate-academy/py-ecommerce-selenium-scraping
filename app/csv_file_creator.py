import csv
from dataclasses import fields

from app.config.parser_config import Product


def csv_file_creator(file_name: str, products: list) -> None:
    with open(f"./{file_name}", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([field.name for field in fields(Product)])
        writer.writerows(products)
