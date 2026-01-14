import logging
import sys


logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout)
    ],
)
