import sys
import zmq
import time
import pickle

import constPipe

#
#   Als 1. Starten
#   pipenv run python reducer.py 1
#   pipenv run python reducer.py 2
#

id = str(sys.argv[1])

context = zmq.Context()
pull_socket = context.socket(zmq.PULL)
pull_socket.bind("tcp://127.0.0.1:" + constPipe.REDUCER_PORT_BASE + id)


time.sleep(1) 

print(f"Start reducer {id}")

counter : dict[str, int] = {}

while True:
    result: str = pickle.loads(pull_socket.recv())

    current_count = counter.get(result, 0)
    current_count += 1
    counter[result] = current_count
    print(f"{result}: {current_count}")