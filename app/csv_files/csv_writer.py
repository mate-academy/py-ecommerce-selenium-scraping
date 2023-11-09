import csv
import os
from app.product import Product


def write_products_to_file(products: list[Product], file_name: str) -> None:
    folder_path = os.path.dirname(__file__)
    os.makedirs(folder_path, exist_ok=True)
    full_file_path = os.path.join(folder_path, file_name)

    with open(full_file_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])
        for product in products:
            writer.writerow([product.title, product.description, product.price, product.rating, product.num_of_reviews])
