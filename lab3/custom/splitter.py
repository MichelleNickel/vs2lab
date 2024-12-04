import zmq
import time
import pickle

import constPipe

#
#   Als 3. Starten
#   pipenv run python splitter.py
#

context = zmq.Context()
push_socket = context.socket(zmq.PUSH)

push_socket.bind("tcp://127.0.0.1:" + constPipe.SPLITTER_PORT)

time.sleep(1) # wait to allow all clients to connect

with open("data.txt", "rt") as file:
    data = file.read()
    for line in data.split("."):
        pretty_line = line.replace("\n", "").replace(",", "").strip()

        print(f"Send: '{pretty_line}'")
        push_socket.send(pickle.dumps(pretty_line))

        time.sleep(0.5)