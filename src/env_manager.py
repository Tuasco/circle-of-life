#!/usr/bin/env false
import signal
from multiprocessing import Queue, Process
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, SHUT_RDWR
from threading import Thread

from parser import parse_command

LISTEN_ADDRESS = "127.0.0.1"
LISTEN_PORT = 15789
LISTEN_LIMIT = 5

class EnvState:
    def __init__(self, send_queue: Queue, recv_queue: Queue):
        # Configure parser and coms with display
        self.send_queue: Queue = send_queue
        self.recv_queue: Queue = recv_queue
        self.parser_thread: Thread = Thread(target=display_listener, args=(self,))
        self.parser_thread.start()
        
        # Configure thread to accept preys and predators
        self.socket_thread: Thread = Thread(target=socket_listener, args=(self,))
        self.socket_thread.start()
        
        # Configure preys and predators processes lists
        self.preys_processes: list[Process] = []
        self.predators_processes: list[Process] = []
        
        #TODO Configure shared memory


def display_listener(env):
    while True:
        command = env.recv_queue.get()
        parse_command(command, env)
        env.send_queue.put('\0')

def socket_listener(env):
    with socket(AF_INET, SOCK_STREAM) as server_socket:
        server_socket.bind((LISTEN_ADDRESS, LISTEN_PORT))
        server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        server_socket.listen(LISTEN_LIMIT)
        
        while True:
            client_socket, client_address = server_socket.accept()
            add_client(env, client_socket, client_address)

def add_client(env: EnvState, client_socket: socket, client_address: tuple[str, int]):
    # Even though it should be the case already, make sure the client IP matches the server's
    if client_address[0] != LISTEN_ADDRESS:
        client_socket.close()
        return
    
    #TODO Share memory with the joined process
    match client_socket.recv(1024).decode().strip():
        case "prey":
            print("sharing memory with new prey")
        case "predator":
            print("sharing memory with new predator")
        case _: pass

    client_socket.shutdown(SHUT_RDWR)
    client_socket.close()

def main(recv_queue: Queue, send_queue: Queue):
    # Catch SIG_INT as display handles it. This file is not meant to be executed anyway, hence the shebang.
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    
    env = EnvState(send_queue, recv_queue)
