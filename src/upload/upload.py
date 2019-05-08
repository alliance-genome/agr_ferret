# Functions for use in downloading files.

import logging, os, requests, json
from requests_toolbelt.utils import dump
from retry import retry
from app import ContextInfo

logger = logging.getLogger(__name__)

@retry(tries=5, delay=5, logger=logger)
def upload_alliance(worker, filename, save_path, data_type, data_sub_type, hash_md5):

    context_info = ContextInfo()

    schema = context_info.config['schema']
    upload_file_prefix = '{}_{}_{}'.format(schema, data_type, data_sub_type)

    # TODO hash_md5 comparison code goes here.

    file_to_upload = {upload_file_prefix: open(save_path + "/" + filename, 'rb')}

    headers = {
        'Authorization': 'Bearer {}'.format(context_info.config['API_KEY'])
    }

    logger.debug('Attempting upload of data file: {}'.format(save_path + '/' + filename, ))
    logger.debug('Attempting upload with header: {}'.format(headers))
    logger.info("{}: Uploading data to {}) ...".format(worker, context_info.config['FMS_URL']))

    response = requests.post(context_info.config['FMS_URL'], files=file_to_upload, headers=headers)
    logger.info(response.text)