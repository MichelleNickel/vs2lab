import rpc
import logging
import time

from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)

cl = rpc.Client()
cl.run()

base_list = rpc.DBList({'foo'})

def print_callback(value):
    print("Result: {}".format(value.value))

cl.append('bar', base_list, print_callback)

for i in range(15):
    print(f"Waiting for {i} seconds")
    time.sleep(1)

cl.stop()
