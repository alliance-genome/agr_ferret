# Decompress compressed files.
import logging, os
logger = logging.getLogger(__name__)

def gunzip_file(**kwargs):
    logger.info('{}: Extracting file with gunzip: {}'.format(kwargs['worker'], kwargs['filename']))
    os.system("gunzip -f {}/{}".format(kwargs['savepath'], kwargs['filename']))

def no_compression(**kwargs):
    logger.info('{}: File suffix \'{}\' not found in decompression dictionary.'.format(kwargs['worker'], kwargs['file_suffix']))
    logger.info('{}: Skipping decompression for {}.'.format(kwargs['worker'], kwargs['filename']))
    pass

# Main function below.
def decompress(worker, filename, savepath):
    # After writing functions for decompression, please add them to this dispatch table by suffix.
    dispatch_dict = {
        'gz': gunzip_file
    }

    file_suffix = filename.split('.')[-1]
    kwargs = {'worker': worker, 'filename': filename, 'savepath': savepath, 'file_suffix': file_suffix}

    # Attempts to lookup a decompression function by file suffix.
    # If the file suffix is not found in the dispatch_dict, it defaults to the no_compression function.
    dispatch_dict.get(file_suffix, no_compression)(**kwargs)