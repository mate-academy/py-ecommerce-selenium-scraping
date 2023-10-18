import csv
import os.path
from pathlib import Path

import pytest

from app.parse import get_all_products, Product


TEST_DIR = Path(__file__).resolve().parent


@pytest.fixture(scope="session", autouse=True)
def run_scraper():
    get_all_products()


@pytest.mark.parametrize("page", ["home", "computers", "phones"])
def test_random_pages_csv_file_is_created(page):
    assert os.path.exists(f"{page}.csv")


@pytest.mark.parametrize("page", ["laptops", "tablets", "touch"])
def test_static_products_are_correct(page):
    with open(TEST_DIR / f"correct_{page}.csv", "r") as correct_file, open(
        f"{page}.csv", "r"
    ) as result_file:
        correct_reader = csv.reader(correct_file)
        result_reader = csv.reader(result_file)

        for correct_row in correct_reader:
            result_row = next(result_reader)

            correct_product = Product(*correct_row)
            result_product = Product(*result_row)

            assert correct_product == result_product
