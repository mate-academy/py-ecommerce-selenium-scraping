import csv
from dataclasses import astuple


def write_elements_to_csv(elements: list, path: str, fields: list) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for element in elements:
            row = list(astuple(element))

            if row and isinstance(row[-1], list):
                row[-1] = ",".join(row[-1]) if row[-1] else ""

            writer.writerow(row)
