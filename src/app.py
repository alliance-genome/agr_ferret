import logging, coloredlogs, yaml, os, sys, urllib3, requests, json
import multiprocessing, time, glob, argparse
from download import *
from upload import *
from compression import *
from cerberus import Validator
import traceback

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--files", type=argparse.FileType('r'), nargs='*',
                    help="Path to files to parse, accepts * as wildcard for filenames")
parser.add_argument('-v', '--verbose', help='Enable verbose mode.', action='store_true')

args = parser.parse_args()
files_to_read = None

if args.files is None:
    files_to_read = glob.glob('src/datasets/*.yaml')
else:
    files_to_read = []
    for entry in args.files:
        files_to_read.append(entry.name)

if args.verbose or ("DEBUG" in os.environ and os.environ['DEBUG'] == "True"):
    debug_level = logging.DEBUG
else:
    debug_level = logging.INFO

coloredlogs.install(level=debug_level,
                    fmt='%(asctime)s %(levelname)s: %(name)s:%(lineno)d: %(message)s',
                    field_styles={
                            'asctime': {'color': 'green'},
                            'hostname': {'color': 'magenta'},
                            'levelname': {'color': 'white', 'bold': True},
                            'name': {'color': 'blue'},
                            'programname': {'color': 'cyan'}
                    })

logging.getLogger("urllib3").setLevel(debug_level)
logger = logging.getLogger(__name__)
http = urllib3.PoolManager()


class FileManager(object):
    
    def __init__(self):
        self.Combined_list_of_dicts = []
        self.validation_schema = None

        # Load validation schema.
        validation_yaml_file_loc = 'src/validation/validation.yaml'
        logger.debug('Loading validation schema: {}'.format(validation_yaml_file_loc))
        validation_schema_file = open(validation_yaml_file_loc, 'r')
        self.validation_schema = yaml.load(validation_schema_file, Loader=yaml.SafeLoader)

        validator = Validator(self.validation_schema)

        # Load and validate yaml(s).
        for filename in files_to_read:
            dataset_file = open(filename, 'r')
            dataset_data = yaml.load(dataset_file, Loader=yaml.FullLoader)
            logger.debug("Loaded yaml data: {}".format(filename))
            logger.info("Validating yaml file: {}".format(filename))
            validation_results = validator.validate(dataset_data)

            if validation_results is True:
                logger.info('Dataset file validation successful.')
            else:
                for field, values in validator.errors.items():
                    logger.critical('Critical error in validation for field: {}.'.format(field))
                    logger.critical(values)
                sys.exit(-1)

            self.Combined_list_of_dicts.append(dataset_data)

    def return_all_dataset_data(self):
        return  self.Combined_list_of_dicts

    def return_datasets(self):
        dataset_list = []
        for entries in self.Combined_list_of_dicts:
            for dataset in entries['datasets']:
                dataset_list.append(dataset)
        return dataset_list


def process_files(dataset, shared_list, finished_list, config_info):
    try:
        _process_files(dataset, shared_list, finished_list, config_info)
    except Exception as e:
        # Re-raise as a plain Exception so multiprocessing can pickle it.
        # urllib HTTPError contains a BufferedReader which is not picklable.
        raise Exception('{}: {}'.format(type(e).__name__, e)) from None


def _process_files(dataset, shared_list, finished_list, config_info):
    process_name = multiprocessing.current_process().name
    url = dataset['url']
    data_type = dataset['type']
    data_sub_type = dataset['subtype']
    filename = dataset['filename']
    save_path = '/usr/src/app/tmp'

    if dataset['status'] == 'active':
        if url not in shared_list and url not in finished_list:
            shared_list.append(url)
            download(process_name, url, filename, save_path)
            shared_list.remove(url)
            if 'filename_uncompressed' in dataset:
                decompress(process_name, filename, save_path)
            finished_list.append(url)
        elif url in finished_list:
            logger.info('{}: URL already downloaded via another process: {}'.format(process_name, url))
        elif url in shared_list:
            logger.info('{}: URL already downloading via another process: {}'.format(process_name, url))
            logger.info('{}: Waiting for other process\'s download to finish.'.format(process_name))
            while url not in finished_list:
                time.sleep(10)

        if 'filename_uncompressed' in dataset:
            filename = dataset['filename_uncompressed']
            logger.info('{}: Found uncompressed filename entry, uploading {}.'
                        .format(process_name, dataset['filename_uncompressed']))
        upload_process(process_name, filename, save_path, data_type, data_sub_type, config_info)


class ProcessManager(object):

    def __init__(self, dataset_info, config_info):
        self.dataset_info = dataset_info  # Datasets with downloadable information.
        self.process_count = config_info.config['threads']  # Number of processes to create.
        self.config_info = config_info  # Bring along our configuration values for later functions.
        self.set_false_when_failed = True # If any process fails, set this to False.

        self.pool = multiprocessing.Pool(processes=self.process_count)  # Create our pool.

    def worker_error(self, e):
        # If we encounter an Exception from one of our workers, log the error.
        logger.error(e)
        self.error_list.append(e)
        self.set_false_when_failed = False

    def start_processes(self):
        manager = multiprocessing.Manager()
        shared_list = manager.list()  # A shared list to track downloading URLs.
        finished_list = manager.list()  # A shared list of finished URLs.
        self.error_list = manager.list() # A shared list of errors. We can't pass this to worker_error so it's "self."
        # Send off all our datasets to the process_files function.
        multiple_results = [self.pool.apply_async(process_files, (x, shared_list, finished_list, self.config_info),
                               error_callback=self.worker_error) for x in self.dataset_info]
        self.pool.close()
        self.pool.join()

        return self.set_false_when_failed, shared_list, self.error_list


# Common configuration variables used throughout the script.
class ContextInfo(object):

    def __init__(self):
        config_file = open('src/config.yaml', 'r')
        self.config = yaml.load(config_file, Loader=yaml.FullLoader)

        # Look for ENV variables to replace default variables from config file.
        for key in self.config.keys():
            try: 
                self.config[key] = os.environ[key]
                logger.info('Found environmental variable for \'{}\'.'.format(key))
            except KeyError:
                logger.info('Environmental variable not found for \'{}\'. Using config.yaml value.'.format(key))
                pass  # If we don't find an ENV variable, keep the value from the config file.
        
        logger.debug('Initialized with config values: {}'.format(self.config))


def post_to_slack(msg):
    config_info = ContextInfo()
    slack_url_component = config_info.config["SLACK_HOOK"]

    url = "https://hooks.slack.com/services/{}".format(slack_url_component)

    mesg = {
        "channel": "#system-alerts",
        "username": "Ferret",
        "text": msg,
        "icon_emoji": ":ferret:"
    }

    http.request('POST', url, body=json.dumps(mesg).encode('utf-8'))

def main():

    config_info = ContextInfo()  # Initialize our configuration values.
    dataset_info = FileManager().return_datasets()  # Initialize our datasets from the dataset files.
    # Begin processing datasets with the ProcessManager.
    did_everything_pass, shared_list, error_list= ProcessManager(dataset_info, config_info).start_processes()

    if did_everything_pass is False:
        failure_message_for_slack = 'When running Ferret, one or more data sources failed to be fetched:\n'
        logger.error('One or more data sources failed to be fetched:')
        for url, error_item in zip(shared_list, error_list):
            # Items that fail will not be removed from the shared_list.
            # Therefore, the shared_list also serves as an "URL error list" in that regard.
            # It *should* match up 1-to-1 for the failed pool processes (the error_list here).
            # If ever the errors do not match up 1-to-1 with the failed URLs, then this assumption is not true.
            logger.error('URL: {} --> Error: {}'.format(url, error_item))
            failure_message_for_slack += 'URL: {} --> Error: {}\n'.format(url, error_item)
        post_to_slack(failure_message_for_slack)

if __name__ == '__main__':
    main()
