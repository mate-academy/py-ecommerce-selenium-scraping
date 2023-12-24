from dataclasses import dataclass, fields


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    @classmethod
    def to_field_list(cls) -> list[str]:
        return [field.name for field in fields(cls)]
