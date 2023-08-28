from app.parser import Parser


def get_all_products() -> None:
    parser = Parser()
    parser.parse()


if __name__ == "__main__":
    get_all_products()
