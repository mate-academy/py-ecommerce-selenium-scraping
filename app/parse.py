from tqdm import tqdm

from app.parse_class import ParseClass

pages = [
    "",
    "computers",
    "phones",
    "phones/touch",
    "computers/tablets",
    "computers/laptops"
]


def get_all_products() -> None:
    for page in tqdm(pages):
        device = ParseClass(page)
        device.parse_processing()


if __name__ == "__main__":
    get_all_products()
