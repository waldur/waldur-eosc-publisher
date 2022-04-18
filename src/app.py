import logging
from time import sleep

import utils

logging.getLogger("requests").setLevel(logging.WARNING)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def sync_offers():
    while True:
        try:
            utils.process_offers()
        except Exception as e:
            logger.error(
                "The application crashed due to the following exception: %s", e
            )
        sleep(60)


if __name__ == "__main__":
    sync_offers()
