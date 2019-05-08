import logging, coloredlogs, yaml, os, sys, json, urllib3, requests, time, random, hashlib
import multiprocessing, time, glob, argparse, itertools
from retry.api import retry_call
from collections import defaultdict
from download import *
from upload import *
from compression import *
from cerberus import Validator

coloredlogs.install(level=logging.DEBUG,
                    fmt='%(asctime)s %(levelname)s: %(name)s:%(lineno)d: %(message)s',
                    field_styles={
                            'asctime': {'color': 'green'},
                            'hostname': {'color': 'magenta'},
                            'levelname': {'color': 'white', 'bold': True},
                            'name': {'color': 'blue'},
                            'programname': {'color': 'cyan'}
                    })

logging.getLogger("urllib3").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--files", type=argparse.FileType('r'), nargs='*', 
help="Path to files to parse, accepts * as wildcard for filenames")

args = parser.parse_args()
files_to_read = None

if args.files is None:
    files_to_read = glob.glob(os.path.join('datasets', '*.yaml'))
else:
    files_to_read = []
    for entry in args.files:
        files_to_read.append(entry.name)

class FileManager(object):
    
    def __init__(self):
        self.Combined_list_of_dicts = []
        self.validation_schema = None

        # Load validation schema.
        validation_yaml_file_loc = os.path.abspath('validation/validation.yaml')
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

def process_files(dataset, shared_list, finished_list):
    process_name = multiprocessing.current_process().name
    url = dataset['url']
    data_type = dataset['type']
    data_sub_type = dataset['subtype']
    filename = dataset['filename']
    save_path = 'files'

    logger.debug('{} is processing {}'.format(process_name, dataset))
    
    if dataset['status'] == 'active':
        if url not in shared_list and url not in finished_list:
            shared_list.append(url)
            download(process_name, url, filename, save_path)
            shared_list.remove(url)
            decompress(process_name, filename, save_path)
            finished_list.append(url)
        elif url in finished_list:
            logger.info('{}: URL already downloaded via another process: {}'.format(process_name, url))
        elif url in shared_list:
            logger.info('{}: URL already downloading via another process: {}'.format(process_name, url))
            logger.info('{}: Waiting for other process\'s download to finish.'.format(process_name))
            while url not in finished_list:
                time.sleep(1)

        # Generate md5
        logger.info('{}: Generating md5 hash for {}.'.format(process_name, filename))
        hash_md5 = hashlib.md5()
        with open(save_path + '/' + filename, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        logger.info('{}: Finished generating md5 hash: {}'.format(process_name, hash_md5.hexdigest()))
            

        upload_alliance(process_name, filename, save_path, data_type, data_sub_type, hash_md5)
        
class ProcessManager(object):

    def __init__(self, process_count, dataset_info, emails):
        self.dataset_info = dataset_info # Datasets with downloadable information.
        self.process_count = process_count # Number of processes to create.
        self.emails = emails # List of email accounts to notify on failure.

    def worker_error(self, e):
        # If we encounter an Exception from one of our workers, terminate the pool and exit immediately.
        # TODO Put email logic here.
        self.pool.terminate()
        logger.error(e)

    def start_processes(self):
        manager = multiprocessing.Manager()
        shared_list = manager.list() # A shared list to track downloading URLs.
        finished_list = manager.list() # A shared list of finished URLs.

        self.pool = multiprocessing.Pool(processes=self.process_count) # Create our pool.
        [self.pool.apply_async(process_files, (x, shared_list, finished_list), error_callback=self.worker_error) for x in self.dataset_info]
        self.pool.close()
        self.pool.join()

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if (cls, args, frozenset(kwargs.items())) not in cls._instances:
            cls._instances[(cls, args, frozenset(kwargs.items()))] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[(cls, args, frozenset(kwargs.items()))]

# Common configuration variables used throughout the script.
class ContextInfo(metaclass=Singleton):
    def __init__(self):
        # Load config file values from file.
        config_file = open('config.yaml', 'r')
        self.config = yaml.load(config_file, Loader=yaml.FullLoader)

        # Look for ENV variables to replace default variables from config file.
        for key in self.config.keys():
            try: 
                self.config[key] = os.environ[key]
            except KeyError:
                pass # If we don't find an ENV variable, keep the value from the config file.
        
        logger.debug('Initialized with config values: {}'.format(self.config))
        logger.info('Retrieval errors will be emailed to: {}'.format(self.config['notification_emails']))            

def main():

    context_info = ContextInfo() # Initialize our configuration values.

    dataset_info = FileManager().return_datasets() # Initialize our datasets from the dataset files.

    # Begin processing datasets with the ProcessManager.
    ProcessManager(context_info.config['threads'], dataset_info, context_info.config['notification_emails']).start_processes()

if __name__ == '__main__':
    main()