import csv
from dataclasses import asdict
from typing import List

from app.models import Product


def write_products_to_csv(
        output_csv_path: str, products: List[Product]
) -> None:
    with open(
            output_csv_path,
            mode="w",
            newline="",
            encoding="utf-8",
    ) as csvfile:

        writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                "title", "description", "price", "rating", "num_of_reviews"
            ]
        )

        writer.writeheader()

        for quote in products:
            writer.writerow(asdict(quote))
