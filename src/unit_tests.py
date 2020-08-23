#!/usr/bin/python3

# When running a script directly, it is impossible to import anything from its parent directory, so can't run unit 
# test from subdirectory in src/<subdir>/ without appending an absolute path to syspath
# 
# To test create_md5 have to add to src/upload/__init__.py 
# from .upload import create_md5
# even though it's not used by the actual code in the agr_ferret/ repo.
#
#
# A live download test, a live create_md5 test off of that file, a generated file and create_md5 test off of that file, 
# and a mock download test that has some issues with namespace.  When the namespace issue is worked out, create more
# mock tests for the rest of the agr_ferret/ repo.
# 
# Run from src/ with 'python unit_tests.py'




import logging, coloredlogs, yaml, os, sys, urllib3, requests
import unittest
import unittest.mock

# importing download from download.download works fine
from download.download import download
# don't need to get download from download.copydl, but later @unittest.mock.patch('download.download.urllib.request') won't work
# from download.copydl import download		# this is not necessary, but if we don't want two copies of the module, we should use this instead

from upload import create_md5


class TestFerret(unittest.TestCase):
    '''Testing the ferret'''

    save_path = '/usr/src/app/tmp'
    download_filename = 'test_download_filename'
    generated_filename = 'test_generated_filename'
    tmp_download_filepath = os.path.join(save_path, download_filename)
    tmp_generated_filepath = os.path.join(save_path, generated_filename)


    def setUp(self):
        # create a file in filesystem to test create_md5 function
        with open(self.tmp_generated_filepath, "w") as f:
            f.write("Delete me!")

# mock.path download.download will cause "ImportError: No module named 'download.download.urllib'; 'download.download' is not a package"
#     @unittest.mock.patch('download.download.urllib.request')	# UNCOMMENT to test failure
# mock.patch download.copydl will use the copied module and work
    @unittest.mock.patch('download.copydl.urllib.request')	# UNCOMMENT to test success
    def test_mock_download(self, mock_urllib_request):
        process_name = 'unittest_mock_download_process'
        url = 'http://tazendra.caltech.edu/~azurebrd/'
        download(process_name, url, self.download_filename, self.save_path)
        mock_urllib_request.urlretrieve.assert_called_with(url, os.path.join(self.save_path, self.download_filename))

    # live test of downloading a file
    def test_live_download(self):
        process_name = 'unittest_live_download_process'
        url = 'http://tazendra.caltech.edu/~azurebrd/'
        download(process_name, url, self.download_filename, self.save_path)
        self.assertTrue(os.path.isfile(self.tmp_download_filepath), "File downloaded")
#         os.remove(tmp_download_filepath)	# to remove downloaded file

    # live test of creating an md5 of a file downloaded to the filesystem
    def test_live_upload_create_md5(self):
        worker = 'unittest_upload_create_md5_worker'
        generated_md5 = create_md5(worker, self.download_filename, self.save_path)
        default_md5 = '2215a61e7f8147cd79edbf6b8f4ebb32'
        self.assertEqual(default_md5, generated_md5)
#         os.remove(tmp_download_filepath)	# to remove downloaded file

    # test create_md5 function off of a file created in the filesystem by this module's setUp 
    def test_generated_upload_create_md5(self):
        worker = 'unittest_upload_create_md5_worker'
        generated_md5 = create_md5(worker, self.generated_filename, self.save_path)
        default_md5 = '58eb258168833030d56510041ac70ebb'
        self.assertEqual(default_md5, generated_md5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
