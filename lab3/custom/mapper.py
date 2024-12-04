import zmq
import pickle

import constPipe

#
#   Als 2. Starten
#   3 mal: pipenv run python mapper.py
#

REDUCER_COUNT = 2

context = zmq.Context()
pull_socket = context.socket(zmq.PULL)
pull_socket.connect("tcp://127.0.0.1:" + constPipe.SPLITTER_PORT)

push_socket_1 = context.socket(zmq.PUSH)
push_socket_2 = context.socket(zmq.PUSH)
push_socket_1.connect("tcp://127.0.0.1:" + constPipe.REDUCER_PORT_BASE + "1")
push_socket_2.connect("tcp://127.0.0.1:" + constPipe.REDUCER_PORT_BASE + "2")

print("Start mapper")

while True:
    sentence: str = pickle.loads(pull_socket.recv())
    print(f"Received: '{sentence}'")

    words = sentence.split(" ")

    for word in words:
        if len(word) == 0:
            continue

        reducer_id = len(word) % REDUCER_COUNT

        print(f"Send '{word}' to {reducer_id}")

        if reducer_id == 0:
            push_socket_1.send(pickle.dumps(word))
        else:
            push_socket_2.send(pickle.dumps(word))