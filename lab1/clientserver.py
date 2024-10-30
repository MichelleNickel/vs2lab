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

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # prevents errors due to "addresses in use"
        self.sock.bind((const_cs.HOST, const_cs.PORT))
        self.sock.settimeout(3)  # time out in order not to block forever
        self._logger.info("Server bound to socket " + str(self.sock))

        # Beispiel In-Memory Telefon-Datenbank
        self.phonebook = {
            "Alpha": "0176-12345678",
            "Beta": "0176-23456789",
            "Gamma": "0176-123123123"
        }

    def serve(self):
        """ Serve echo """
        self.sock.listen(1)
        while self._serving:  # as long as _serving (checked after connections or socket timeouts)
            try:
                # pylint: disable=unused-variable
                (connection, address) = self.sock.accept()  # returns new socket and address of client
                while True:  # forever
                    data = connection.recv(1024).decode('utf-8')  # receive data from client and decode it
                    if not data:
                        break  # stop if client stopped
                    response = self.handle_request(data)
                    connection.send(response.encode('utf-8')) # return encoded response
                connection.close()  # close the connection
            except socket.timeout:
                pass  # ignore timeouts
        self.sock.close()
        self._logger.info("Server down.")

    def handle_request(self, request):
        """ handle client requests """
        # If GETALL request:
        if request.startswith("GETALL"):
            # Return all Entries
            return str(self.phonebook)
        # If GET request:
        elif request.startswith("GET"):
            # Extrahiere den Namen
            name = request.split(" ")[1]
            return self.phonebook.get(name, "404 Name not found.")
        else:
            return "Request unknown."


class Client:
    """ The client """
    logger = logging.getLogger("vs2lab.a1_layers.clientserver.Client")

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((const_cs.HOST, const_cs.PORT))
        self.logger.info("Client connected to socket " + str(self.sock))

    def call(self, msg_in="Hello, world"):
        """ Call server """
        self.sock.send(msg_in.encode('ascii'))  # send encoded string as data
        data = self.sock.recv(1024)  # receive the response
        msg_out = data.decode('ascii')
        print(msg_out)  # print the result
        self.sock.close()  # close the connection
        self.logger.info("Client down.")
        return msg_out
    
    # GET function
    def get(self, name):
        """ Requests the Phone number for a specific name """
        self.sock.send(f"GET {name}".encode('utf-8')) # Formatted string with the name
        data = self.sock.recv(1024).decode('utf-8') # Decode the response
        print("Antwort vom Server:", data) # Print out the answer
        return data

    # GETALL function
    def get_all(self):
        """ Requests the entire phonebooks data """
        self.sock.send("GETALL".encode('utf-8')) # Encode GETALL String and send it to the server
        data = self.sock.recv(1024).decode('utf-8') # Decode response 
        print("Antwort vom Server:", data) # Print out the answer
        return data

    def close(self):
        """ Close socket """
        self.sock.close()
