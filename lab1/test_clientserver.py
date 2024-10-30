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

    def test_get_empty_name(self):
        msg = self.client.get("")
        self.assertEqual(msg, "ERR;NoEntry")

    def test_get_existing_name(self):
        msg = self.client.get("Günter")
        self.assertEqual(msg, "OK;Günter%71731")

    def test_get_non_existing_name(self):
        msg = self.client.get("Peter")
        self.assertEqual(msg, "ERR;NoEntry")

    def test_get_all(self):
        msg = self.client.get_all()
        self.assertEqual(msg, "OK;Hans%12313131313;Jutta%83717271;Günter%71731")

    def test_call_empty_string(self):
        msg =self.client._call(" ")
        self.assertEqual(msg, "ERR;InvalidCommand")

    def test_call_malformed_command(self):
        msg =self.client._call(";;GETALL")
        self.assertEqual(msg, "ERR;InvalidCommand")

    def test_call_get_with_no_args_command(self):
        msg =self.client._call("GET")
        self.assertEqual(msg, "ERR;NoName")

    def tearDown(self):
        self.client.close()  # terminate client after each test

    @classmethod
    def tearDownClass(cls):
        cls._server._serving = False  # break out of server loop. pylint: disable=protected-access
        cls._server_thread.join()  # wait for server thread to terminate


if __name__ == '__main__':
    unittest.main()
