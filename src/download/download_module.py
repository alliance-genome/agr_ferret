# Functions for use in downloading files.

import logging, os
import urllib
from retry import retry

logger = logging.getLogger(__name__)


@retry(tries=5, delay=5, logger=logger)
def download(worker, url, filename, savepath):
    logger.info("{}: Downloading data from {}) ... " . format(worker, url))
    urllib.request.urlretrieve(url, os.path.join(savepath, filename))
    logger.info("finished download: " + filename)
