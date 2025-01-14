"""
Simple client server unit test
"""

import logging
import threading
import unittest

import clientserver
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)


class TestEchoService(unittest.TestCase):
    """The test"""
    _server = clientserver.Server()  # create single server in class variable
    _server_thread = threading.Thread(target=_server.serve)  # define thread for running server

    @classmethod
    def setUpClass(cls):
        cls._server_thread.start()  # start server loop in a thread (called only once)

    def setUp(self):
        super().setUp()
        self.client = clientserver.Client()  # create new client for each test

    def test_srv_get(self):  # each test_* function is a test
        """Test simple call"""
        msg = self.client.call("Hello VS2Lab")
        self.assertEqual(msg, 'Hello VS2Lab*')

    def test_get(self): # test for get-function
        """Test get-function"""
        msg = self.client.get("Alpha")
        self.assertEqual(msg, '0176-12345678')

    def test_get(self): # test for get-function
        """Test get-function"""
        msg = self.client.get("Beta")
        self.assertEqual(msg, '0176-23456789')

    def test_get(self): # test for get-function
        """Test get-function"""
        msg = self.client.get("Gamma")
        self.assertEqual(msg, '0176-123123123')

    def test_getall(self): # test for getall-function
        """Test get-all-function"""
        msg = self.client.get_all()
        phonebook = "{'Alpha': '0176-12345678', 'Beta': '0176-23456789', 'Gamma': '0176-123123123'}"
        self.assertEqual(msg, phonebook)

    def tearDown(self):
        self.client.close()  # terminate client after each test

    @classmethod
    def tearDownClass(cls):
        cls._server._serving = False  # break out of server loop. pylint: disable=protected-access
        cls._server_thread.join()  # wait for server thread to terminate


if __name__ == '__main__':
    unittest.main()
