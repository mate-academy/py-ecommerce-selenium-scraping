from dataclasses import dataclass


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


if __name__ == "__main__":
    print("$809.00".split("$"))
