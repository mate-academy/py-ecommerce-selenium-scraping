import csv
from dataclasses import astuple


class CSVFileWriter:
    def __init__(self, file_name: str, column_fields: [str]) -> None:
        self.file_name = file_name
        self.column_fields = column_fields

    def write_in_csv_file(self, data: list) -> None:
        with open(
            self.file_name + ".csv", "w", encoding="utf-8", newline=""
        ) as file:
            writer = csv.writer(file)
            writer.writerow(self.column_fields)
            writer.writerows([astuple(record) for record in data])
