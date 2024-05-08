import csv
from pathlib import Path

from app.product_class import Product, PRODUCT_FIELDS


def write_to_csv(path_to_file: str, data: list[Product]) -> None:
    path = Path(path_to_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        for product in data:
            writer.writerow(
                getattr(product, field) for field in PRODUCT_FIELDS
            )
