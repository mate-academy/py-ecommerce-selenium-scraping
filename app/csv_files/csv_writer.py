import csv

from app.product import Product


def write_products_to_file(products: list[Product], file_name: str) -> None:
    with open(file_name, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])
        for product in products:
            writer.writerow([product.title, product.description, product.price, product.rating, product.num_of_reviews])
