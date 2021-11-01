import logging
import utils


logging.getLogger("requests").setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO, format=f'[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - '
                                               f'%(message)s')


def sync_offers():
    utils.process_offers()
    logging.info('process_offers is finished.')
    return "The offers were synced"


if __name__ == '__main__':
    sync_offers()
