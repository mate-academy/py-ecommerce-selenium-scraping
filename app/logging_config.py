import logging
import sys


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(levelname)8s]: %(message)s",
        handlers=[
            logging.FileHandler("parser.log", mode="w"),
            logging.StreamHandler(sys.stdout),
        ]
    )
