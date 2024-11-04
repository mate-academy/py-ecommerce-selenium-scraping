class CSVGenerator:

    @staticmethod
    def get_csv_path() -> str:
        csv_files = [
            "home.csv",
            "computers.csv",
            "laptops.csv",
            "tablets.csv",
            "phones.csv",
            "touch.csv",
        ]
        for filename in csv_files:
            yield filename
