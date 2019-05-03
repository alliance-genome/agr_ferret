import logging, coloredlogs, yaml, os, sys, json, urllib3, requests, time, random
import multiprocessing, time, glob
from collections import defaultdict
from download import *
from compression import *

# from cerberus import Validator

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

class FileManager(object):
    
    def __init__(self, config_file_dir):
        self.Combined_list_of_dicts = []

        # Loading yaml(s).
        logger.info('Loading yaml file(s): %s' % config_file_dir)
        for filename in glob.glob(os.path.join(config_file_dir, '*.yaml')):
            config_file = open(filename, 'r')
            config_data = yaml.load(config_file, Loader=yaml.FullLoader)
            logger.debug("Loaded yaml data: %s" % config_data)
            self.Combined_list_of_dicts.append(config_data)

    def return_all_config_data(self):
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
    dataset_info = FileManager('config').return_datasets()

    ProcessManager(5, dataset_info).start_processes()

if __name__ == '__main__':
    main()