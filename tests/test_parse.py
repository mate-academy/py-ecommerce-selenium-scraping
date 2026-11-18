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
    with (
        open(TEST_DIR / f"correct_{page}.csv", "r") as correct_file,
        open(f"{page}.csv", "r") as result_file,
    ):
        correct_rows = list(csv.reader(correct_file))
        result_rows = list(csv.reader(result_file))

    assert len(result_rows) == len(correct_rows)

    for correct_row, result_row in zip(correct_rows, result_rows):
        assert Product(*correct_row) == Product(*result_row)
