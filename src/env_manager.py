#!/usr/bin/env python3
from multiprocessing import Queue
from threading import Thread
from parser import parse_command

class EnvState:
    def __init__(self, send_queue: Queue, recv_queue: Queue):
        # Configure parser and coms with display
        self.send_queue: Queue = send_queue
        self.recv_queue: Queue = recv_queue
        self.parser_thread: Thread = Thread(target=display_listener, args=(self,))
        self.parser_thread.start()
        

def display_listener(env):
    while True:
        command = env.recv_queue.get()
        parse_command(command, env)
        env.send_queue.put('\0')
        
def main(recv_queue: Queue, send_queue: Queue):
    env = EnvState(send_queue, recv_queue)