import csv

from app.logger.logger import logging
from app.model.product import PRODUCT_FIELDS, astuple


def write_items_to_csv(items: list, path: str) -> None:
    logging.info(f"Start writing products to csv {path}")
    with open(path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(item) for item in items)
        logging.info(f"Successfully wrote products to csv {path}")
