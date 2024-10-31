"""
Client and server using classes
"""

import logging
import socket

import const_cs
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)  # init loging channels for the lab

# pylint: disable=logging-not-lazy, line-too-long

class Server:
    """ The server """
    _logger = logging.getLogger("vs2lab.lab1.clientserver.Server")
    _serving = True

    _db = {
        "Hans": "12313131313",
        "Jutta": "83717271",
        "Günter": "71731"
    }

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # prevents errors due to "addresses in use"
        self.sock.bind((const_cs.HOST, const_cs.PORT))
        self.sock.settimeout(3)  # time out in order not to block forever
        self._logger.info("Server bound to socket " + str(self.sock))


    def _handle_get(self, args: list[str]) -> str:
        if len(args) == 0:
            return "ERR;NoName"

        name = args[0]

        value = self._db.get(name, None)

        if not value:
            return "ERR;NoEntry"

        return f"OK;{name}%{value}"

    def _handle_get_all(self) -> str:
        return "OK;" + ";".join([f"{name}%{value}" for name, value in self._db.items()])

    def _handle(self, msg: str) -> str:
        args = msg.split(";")
        cmd = args[0]

        if cmd == "GET":
            return self._handle_get(args[1:])
        elif cmd == "GETALL":
            return self._handle_get_all()

        return "ERR;InvalidCommand"

    def serve(self):
        """ Serve echo """
        self.sock.listen(1)
        while self._serving:  # as long as _serving (checked after connections or socket timeouts)
            try:
                # pylint: disable=unused-variable
                (connection, address) = self.sock.accept()  # returns new socket and address of client
                while True:  # forever
                    data = connection.recv(1024)  # receive data from client
                    if not data:
                        break  # stop if client stopped

                    request = data.decode('utf-8')
                    self._logger.info(f"Received request: {request}")
                    response = self._handle(request) + ";END"
                    self._logger.info(f"Send response: {response}")
                    connection.send(response.encode('utf-8'))
                connection.close()  # close the connection
            except socket.timeout:
                pass  # ignore timeouts
        self.sock.close()
        self._logger.info("Server down.")


class Client:
    """ The client """
    logger = logging.getLogger("vs2lab.a1_layers.clientserver.Client")

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((const_cs.HOST, const_cs.PORT))
        self.logger.info("Client connected to socket " + str(self.sock))

    def get(self, name: str):
        cmd = f"GET;{name}"
        return self._call(cmd)

    def get_all(self):
        cmd = "GETALL"
        return self._call(cmd)

    def _call(self, msg: str) -> str:
        """ Call server """
        self.sock.send(msg.encode('utf-8'))  # send encoded string as data
        self.logger.info(f"Send message: {msg}")

        response = ""

        while not response.endswith(";END"):
            data = self.sock.recv(1024)  
            response += data.decode('utf-8')

        self.logger.info(f"Received message: {response}")
        return response

    def close(self):
        """ Close socket """
        self.sock.close()
        self.logger.info("Client closed.")
