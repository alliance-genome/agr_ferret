# Functions for use in downloading files.

import logging, os
import urllib.request
from retry import retry

logger = logging.getLogger(__name__)


@retry(tries=5, delay=5, logger=logger)
def download(worker, url, filename, savepath):
    logger.info("{}: Downloading data from {} ... " . format(worker, url))
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (AGR Ferret)'})
    resp = urllib.request.urlopen(req, timeout=120)
    with open(os.path.join(savepath, filename), 'wb') as f:
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            f.write(chunk)
    logger.info("finished download: " + filename)
