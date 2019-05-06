# Functions for use in downloading files.

import logging, os, urllib
from retry import retry
from app import ContextInfo

logger = logging.getLogger(__name__)

@retry(tries=5, delay=5, logger=logger)
def upload_alliance(worker, url, filename, savepath):
    logger.info("{}: Uploading data to {}) ...".format(worker, url))
    urllib.request.urlretrieve(url, savepath + "/" + filename)