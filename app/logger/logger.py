# import logging
# import sys
#
#
# logging.basicConfig(
#     level=logging.ERROR,
#     format="%(asctime)s - %(levelname)s - %(message)s",
#     handlers=[
#         logging.FileHandler("parser.log"),
#         logging.StreamHandler(sys.stdout)
#     ],
# )
import logging
from tqdm import tqdm

class TqdmLoggingHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        tqdm.write(msg)

handler = TqdmLoggingHandler()
logging.basicConfig(
    level=logging.WARNING,
    handlers=[handler],
    format="%(asctime)s - %(levelname)s - %(message)s"
)