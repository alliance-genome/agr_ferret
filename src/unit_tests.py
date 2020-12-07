#!/usr/bin/python3

# When running a script directly, it is impossible to import anything from its parent directory, so can't run unit 
# test from subdirectory in src/<subdir>/ without appending an absolute path to syspath
# 
# To test create_md5 have to add to src/upload/__init__.py 
# from .upload import create_md5
# even though it's not used by the actual code in the agr_ferret/ repo.
#
# A live download test, a live create_md5 test off of that file, a generated file and create_md5 test off of that file, 
# and a mock download test that has some issues with namespace.  When the namespace issue is worked out, create more
# mock tests for the rest of the agr_ferret/ repo.
# 
# Using python 3.6+ run from repo's root with 'python src/unit_tests.py'


import logging, coloredlogs, yaml, os, sys, urllib3, requests
import multiprocessing, time, glob, argparse
import unittest, unittest.mock

from download.download_module import download
from upload.upload import create_md5, upload_file, upload_process
from compression.compression import gunzip_file, unzip_file, no_compression, decompress

# from download import *
# from upload import *
# from compression import *

from app import main, ContextInfo, ProcessManager, FileManager, process_files

# from download import *
# from upload import *


class TestFerret(unittest.TestCase):
    '''Testing the ferret'''

    save_path = '/usr/src/app/tmp'
    generated_filename = 'test_generated_filename'
    tmp_generated_filepath = os.path.join(save_path, generated_filename)
    config_info = ContextInfo()
    kwargs = {'worker': 'worker', 'filename': 'filename', 'savepath': 'savepath', 'file_suffix': 'file_suffix'}

# # new
#     manager = multiprocessing.Manager()
#     shared_list = manager.list()  # A shared list to track downloading URLs.
#     finished_list = manager.list()  # A shared list of finished URLs.

#     dataset_info = FileManager().return_datasets()
#     process_manager = ProcessManager(dataset_info, config_info)
# 
# # end new


    def setUp(self):
        # create a file in filesystem to test create_md5 function
        with open(self.tmp_generated_filepath, "w") as f:
            f.write("Delete me!")

    # in progress
# #     @unittest.mock.patch('app.process_files')
# #     @unittest.mock.patch('upload.upload.json')
# #     @unittest.mock.patch('upload.upload.urllib.request')
# #     @unittest.mock.patch('upload.upload_module.upload_process')
# 
# #     @unittest.mock.patch('app.upload_process')
# # this doesn't work, NameError: name 'upload_process' is not defined
#     @unittest.mock.patch('app.download')
#     def test_mock_process_files(self, mock_app_download):
# #     def test_mock_process_files(self, mock_app_download, mock_app_upload_process):
#         process_name = 'unittest_mock_process_files'
#         dataset = self.dataset_info[0]
#         process_files(dataset, self.shared_list, self.finished_list, self.config_info)
# #         upload_process(process_name, self.generated_filename, self.save_path, 'data_type', 'data_sub_type', self.config_info)
# #         mock_urllib_request.urlopen.assert_called()
# #         mock_json.loads.assert_called()

    # mock tests

    @unittest.mock.patch('app.ContextInfo')
    @unittest.mock.patch('app.FileManager.return_datasets')
    @unittest.mock.patch('app.ProcessManager.start_processes', return_value=True)
    def test_mock_app_main(self, mock_process_manager, mock_file_manager, mock_context_info):
        process_name = 'unittest_mock_app_main'
        main()
        mock_process_manager.assert_called()
 
    @unittest.mock.patch('sys.exit')
    @unittest.mock.patch('app.ContextInfo')
    @unittest.mock.patch('app.FileManager.return_datasets')
    @unittest.mock.patch('app.ProcessManager.start_processes', return_value=False)
    def test_mock_app_main_sys_exit(self, mock_process_manager, mock_file_manager, mock_context_info, mock_sys_exit):
        process_name = 'unittest_mock_app_main_sys_exit'
        main()
        mock_sys_exit.assert_called_with(-1)

    @unittest.mock.patch('app.download')
    @unittest.mock.patch('app.upload_process')
    def test_mock_process_files_url_not_in(self, mock_app_upload_process, mock_app_download):
        process_name = 'unittest_mock_process_files_url_not_in'
        manager = multiprocessing.Manager()
        shared_list = manager.list() 
        finished_list = manager.list() 
        dataset = {'status': 'active', 'url': 'url', 'filename': 'filename', 'type': 'datatype', 'subtype': 'datasubtype'}
        process_files(dataset, shared_list, finished_list, None)
        mock_app_upload_process.assert_called()

    @unittest.mock.patch('app.decompress')
    @unittest.mock.patch('app.download')
    @unittest.mock.patch('app.upload_process')
    def test_mock_process_files_uncompressed(self, mock_app_upload_process, mock_app_download, mock_decompress):
        process_name = 'unittest_mock_process_files_uncompressed'
        manager = multiprocessing.Manager()
        shared_list = manager.list() 
        finished_list = manager.list() 
        dataset = {'status': 'active', 'url': 'url', 'filename': 'filename', 'type': 'datatype', 'subtype': 'datasubtype', 'filename_uncompressed': 'wb.gaf'}
        process_files(dataset, shared_list, finished_list, None)
        mock_decompress.assert_called()

    @unittest.mock.patch('app.download')
    @unittest.mock.patch('app.upload_process')
    def test_mock_process_files_finished_list(self, mock_app_upload_process, mock_app_download):
        process_name = 'unittest_mock_process_files_finished_list'
        dataset = {'status': 'active', 'url': 'url', 'filename': 'filename', 'type': 'datatype', 'subtype': 'datasubtype'}
        manager = multiprocessing.Manager()
        shared_list = manager.list() 	# A shared list to track downloading URLs.
        finished_list = manager.list() 	# A shared list of finished URLs.
        finished_list.append(dataset['url'])
        process_files(dataset, shared_list, finished_list, None)
        mock_app_upload_process.assert_called()

    @unittest.mock.patch('time.sleep')
    @unittest.mock.patch('app.download')
    @unittest.mock.patch('app.upload_process')
    def test_mock_process_files_shared_list(self, mock_app_upload_process, mock_app_download, mock_time_sleep):
        process_name = 'unittest_mock_process_files_shared_list'
        dataset = {'status': 'active', 'url': 'url', 'filename': 'filename', 'type': 'datatype', 'subtype': 'datasubtype'}
        pool = multiprocessing.Pool(processes=2)  # Create our pool.
        manager = multiprocessing.Manager()
        shared_list = manager.list()            # A shared list to track downloading URLs.
        finished_list = manager.list()          # A shared list of finished URLs.
        shared_list.append(dataset['url'])
        pool.apply_async( process_files, (dataset, shared_list, finished_list, None))
        finished_list.append(dataset['url'])
        pool.apply_async( process_files, (dataset, shared_list, finished_list, None))
        pool.close()
        pool.join()
        mock_time_sleep.assert_called()

    @unittest.mock.patch('download.download_module.urllib.request')
    def test_mock_download(self, mock_urllib_request):
        process_name = 'unittest_mock_download_process'
        url = 'mock_url'
        download(process_name, url, self.generated_filename, self.save_path)
        mock_urllib_request.urlretrieve.assert_called_with(url, os.path.join(self.save_path, self.generated_filename))
 
    @unittest.mock.patch('upload.upload.hashlib')
    def test_mock_upload_create_md5(self, mock_hashlib):
        process_name = 'unittest_mock_upload_create_md5'
        create_md5(process_name, self.generated_filename, self.save_path)
        mock_hashlib.md5().update.assert_called()
 
    @unittest.mock.patch('upload.upload.requests')
    def test_mock_upload_upload_file(self, mock_requests):
        process_name = 'unittest_mock_upload_upload_file'
        upload_file(process_name, self.generated_filename, self.save_path, 'upload_file_prefix', self.config_info)
        mock_requests.post.assert_called()
 
    @unittest.mock.patch('upload.upload.json')
    @unittest.mock.patch('upload.upload.urllib.request')
    @unittest.mock.patch('upload.upload.upload_file')
    @unittest.mock.patch('upload.upload.create_md5')
    def test_mock_upload_upload_process_not_chip_data(self, mock_create_md5, mock_upload_file, mock_urllib_request, mock_json):
        process_name = 'unittest_mock_upload_upload_process_not_chip_data'
        mock_create_md5.return_value = 'generated_dummy'
        mock_json.loads.return_value = None
        upload_process(process_name, self.generated_filename, self.save_path, 'data_type', 'data_sub_type', self.config_info)
        mock_upload_file.assert_called()
 
    @unittest.mock.patch('upload.upload.json')
    @unittest.mock.patch('upload.upload.urllib.request')
    @unittest.mock.patch('upload.upload.create_md5')
    def test_mock_upload_upload_process_chip_data_existing_same(self, mock_create_md5, mock_urllib_request, mock_json):
        process_name = 'unittest_mock_upload_upload_process_chip_data_existing_same'
        mock_create_md5.return_value = 'same_md5Sum'
        mock_json.loads.return_value = [{'md5Sum': 'same_md5Sum'}]
        upload_process(process_name, self.generated_filename, self.save_path, 'data_type', 'data_sub_type', self.config_info)
 
    @unittest.mock.patch('upload.upload.json')
    @unittest.mock.patch('upload.upload.urllib.request')
    @unittest.mock.patch('upload.upload.upload_file')
    @unittest.mock.patch('upload.upload.create_md5')
    def test_mock_upload_upload_process_chip_data_existing_different(self, mock_create_md5, mock_upload_file, mock_urllib_request, mock_json):
        process_name = 'unittest_mock_upload_upload_process_chip_data_existing_different'
        mock_create_md5.return_value = 'generated_dummy'
        mock_json.loads.return_value = [{'md5Sum': 'existing_dummy'}]
        upload_process(process_name, self.generated_filename, self.save_path, 'data_type', 'data_sub_type', self.config_info)
        mock_upload_file.assert_called()
 
    @unittest.mock.patch('upload.upload.json')
    @unittest.mock.patch('upload.upload.urllib.request')
    @unittest.mock.patch('upload.upload.upload_file')
    @unittest.mock.patch('upload.upload.create_md5')
    def test_mock_upload_upload_process_chip_data_not_existing(self, mock_create_md5, mock_upload_file, mock_urllib_request, mock_json):
        process_name = 'unittest_mock_upload_upload_process_chip_data_not_existing'
        mock_create_md5.return_value = 'generated_dummy'
        mock_json.loads.return_value = [{'NO-md5Sum': 'existing_dummy'}]
        upload_process(process_name, self.generated_filename, self.save_path, 'data_type', 'data_sub_type', self.config_info)
        mock_upload_file.assert_called()
 
    @unittest.mock.patch('compression.compression.os')
    def test_mock_compression_compression_gunzip_file(self, mock_os):
        gunzip_file(**self.kwargs)
        mock_os.system.assert_called()
 
    @unittest.mock.patch('compression.compression.os')
    def test_mock_compression_compression_unzip_file(self, mock_os):
        unzip_file(**self.kwargs)
        mock_os.system.assert_called()
 
    @unittest.mock.patch('compression.compression.logger')
    def test_mock_compression_compression_logger(self, mock_logger):
        no_compression(**self.kwargs)
        mock_logger.info.assert_called_with('{}: Skipping decompression for {}.'.format(self.kwargs['worker'], self.kwargs['filename']))
 
    @unittest.mock.patch('compression.compression.gunzip_file')
    def test_mock_compression_compression_decompress_gunzip_file(self, mock_gunzip_file):
        decompress('worker', 'filename.gz', 'savepath')
        mock_gunzip_file.assert_called()
 
    @unittest.mock.patch('compression.compression.unzip_file')
    def test_mock_compression_compression_decompress_unzip_file(self, mock_unzip_file):
        decompress('worker', 'filename.zip', 'savepath')
        mock_unzip_file.assert_called()
 
    @unittest.mock.patch('compression.compression.no_compression')
    def test_mock_compression_compression_decompress_no_compression(self, mock_no_compression):
        decompress('worker', 'filename', 'savepath')
        mock_no_compression.assert_called()
 
 
 
    # live tests
    # test create_md5 function off of a file created in the filesystem by this module's setUp 
    def test_generated_upload_create_md5(self):
        worker = 'unittest_upload_create_md5_worker'
        generated_md5 = create_md5(worker, self.generated_filename, self.save_path)
        default_md5 = '58eb258168833030d56510041ac70ebb'
        self.assertEqual(default_md5, generated_md5)
        # os.remove(tmp_generated_filepath)	# to remove downloaded file


if __name__ == '__main__':
    unittest.main(verbosity=2)
