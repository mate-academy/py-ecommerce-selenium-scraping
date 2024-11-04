import csv


def save_quotes_to_csv(products: list, output_csv_path: str) -> None:
    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "title",
            "description",
            "price",
            "rating",
            "num_of_reviews"])
        for product in products:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews,
                ]
            )
