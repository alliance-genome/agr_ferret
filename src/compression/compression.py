# Decompress compressed files.
import logging, os
logger = logging.getLogger(__name__)

def decompress(worker, filename, savepath):
    dispatch_dict = {
        'gz' : gunzip_file(worker, filename, savepath)
    }

    dispatch_dict[filename.split('.')[-1]]

def gunzip_file(worker, filename, savepath):
    logger.info('{}: Extracting file with gunzip: {}'.format(worker, filename))
    os.system("gunzip -f {}/{}".format(savepath, filename))