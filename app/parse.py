from app.scrapper import Scrapper


def main() -> None:
    scrapper = Scrapper()
    scrapper.get_all_products()


if __name__ == "__main__":
    main()
