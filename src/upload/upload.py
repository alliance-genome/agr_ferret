# Functions for use in downloading files.

import logging, os, requests, json, hashlib, urllib
from requests_toolbelt.utils import dump
from retry import retry

logger = logging.getLogger(__name__)


def create_md5(worker, filename, save_path):
    # Generate md5
    logger.info('{}: Generating md5 hash for {}.'.format(worker, filename))
    hash_md5 = hashlib.md5()
    with open(os.path.join(save_path, filename), 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
    logger.info('{}: Finished generating md5 hash: {}'.format(worker, hash_md5.hexdigest()))

    return hash_md5.hexdigest()


def upload_file(worker, filename, save_path, upload_file_prefix, config_info):
    file_to_upload = {upload_file_prefix: open(os.path.join(save_path, filename), 'rb')}

    headers = {
        'Authorization': 'Bearer {}'.format(config_info.config['API_KEY'])
    }

    logger.debug('{}: Attempting upload of data file: {}'.format(worker, os.path.join(save_path, filename)))
    logger.debug('{}: Attempting upload with header: {}'.format(worker, headers))
    logger.info("{}: Uploading data to {}) ...".format(worker, config_info.config['FMS_API_URL']+'/api/data/submit/'))

    response = requests.post(config_info.config['FMS_API_URL']+'/api/data/submit/', files=file_to_upload, headers=headers)
    logger.info(response.text)


@retry(tries=5, delay=5, logger=logger)
def upload_process(worker, filename, save_path, data_type, data_sub_type, config_info):

    release = config_info.config['ALLIANCE_RELEASE']
    upload_file_prefix = '{}_{}_{}'.format(release, data_type, data_sub_type)

    generated_md5 = create_md5(worker, filename, save_path)

    # Attempt to grab MD5 for the latest version of the file.
    logger.debug(config_info.config['FMS_API_URL'] + '/api/datafile/by/{}/{}?latest=true'.format(data_type, data_sub_type))
    url_to_check = config_info.config['FMS_API_URL'] + '/api/datafile/by/{}/{}?latest=true'.format(data_type, data_sub_type)
    chip_response = urllib.request.urlopen(url_to_check)
    chip_data = data = json.loads(chip_response.read().decode(chip_response.info().get_param('charset') or 'utf-8'))
    logger.debug('{}: Retrieved API data from chipmunk: {}'.format(worker, chip_data))

    # Check for existing MD5
    logger.info('{}: Checking for existing MD5 from chipmunk.'.format(worker))

    # Logic for uploading new files based on existing and new MD5s.
    if not chip_data:
        logger.info('{}: No response received from the FMS. A new file will be uploaded.'.format(worker))
        logger.info('{}: File: {}'.format(worker, filename))
        upload_file(worker, filename, save_path, upload_file_prefix, config_info)
    else:
        existing_md5 = chip_data[0].get('md5Sum')
        if existing_md5:
            logger.info('{}: Previous MD5 found: {}'.format(worker, existing_md5))
            if existing_md5 == generated_md5:
                logger.info('{}: Existing MD5 matches the newly generated MD5. The file will not be uploaded.'.format(worker))
                logger.info('{}: File: {}'.format(worker, filename))
                logger.info('{}: Existing: {} New: {}'.format(worker, existing_md5, generated_md5))
            else:
                logger.info('{}: Existing MD5 does not match the newly generated MD5. A new file will be uploaded.'.format(worker))
                logger.info('{}: File: {}'.format(worker, filename))
                logger.info('{}: Existing: {} New: {}'.format(worker, existing_md5, generated_md5))
                upload_file(worker, filename, save_path, upload_file_prefix, config_info)
        else:
            logger.info('{}: Existing MD5 not found. A new file will be uploaded.'.format(worker))
            logger.info('{}: File: {}'.format(worker, filename))
            logger.info('{}: Existing: {} New: {}'.format(worker, existing_md5, generated_md5))
            upload_file(worker, filename, save_path, upload_file_prefix, config_info)
