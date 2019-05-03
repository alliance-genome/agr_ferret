import logging, coloredlogs, yaml, os, sys, json, urllib3, requests, time, random
import multiprocessing, time, glob, argparse, itertools
from collections import defaultdict
from download import *
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

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--files", type=argparse.FileType('r'), nargs='*', 
help="Path to files to parse, accepts * as wildcard for filenames")

args = parser.parse_args()
files_to_read = None

if args.files is None:
    files_to_read = glob.glob(os.path.join('dataset', '*.yaml'))
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

def process_files(dataset):
    process_name = multiprocessing.current_process().name
    url = dataset['url']
    filename = dataset['filename']
    savepath = 'files'

    logger.debug('{} is processing {}'.format(process_name, dataset))
    
    if dataset['status'] == 'active':
        download_http(process_name, url, filename, savepath)
        decompress(process_name, filename, savepath)


class ProcessManager(object):

    def __init__(self, process_count, dataset_info):
        self.dataset_info = dataset_info # Datasets with downloadable information.
        self.process_count = process_count # Number of processes to create.

    def worker_error(self, e):
        # If we encounter an Exception from one of our workers, terminate the pool and exit immediately.
        self.pool.terminate()
        logger.error(e)

    def start_processes(self):
        self.pool = multiprocessing.Pool(processes=self.process_count) # Create our pool.
        [self.pool.apply_async(process_files, (x,), error_callback=self.worker_error) for x in self.dataset_info]
        self.pool.close()
        self.pool.join()

def main():
    dataset_info = FileManager().return_datasets()

    ProcessManager(5, dataset_info).start_processes()

if __name__ == '__main__':
    main()