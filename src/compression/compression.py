# Decompress compressed files.
import logging, os
logger = logging.getLogger(__name__)

def gunzip_file(**kwargs):
    logger.info('{}: Extracting file with gunzip: {}'.format(kwargs['worker'], kwargs['filename']))
    os.system("gunzip -f {}/{}".format(kwargs['savepath'], kwargs['filename']))

def pass_func(**kwargs):
    logger.info('{}: Skipping decompression for {}.'.format(kwargs['worker'], kwargs['filename']))
    pass

# Main function below.
def decompress(worker, filename, savepath):
    # After writing functions for decompression, please add them to this dispatch table by suffix.
    dispatch_dict = {
        'gz' : gunzip_file,
        'json' : pass_func
    }

    kwargs = {'worker': worker, 'filename': filename, 'savepath': savepath}
    dispatch_dict.get(filename.split('.')[-1])(**kwargs)