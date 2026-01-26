#!/usr/bin/env false
import mmap
import signal
import struct
from multiprocessing import Process
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, SHUT_RDWR
from threading import Thread

import posix_ipc

from individual import IndividualType
from message_queue import MessageQueue
from parser import parse_command

LISTEN_ADDRESS = "127.0.0.1"
LISTEN_PORT = 15789
LISTEN_LIMIT = 5

POPULATION_LIMIT = 10
GRASS_LIMIT = 4
SHM_NAME = "/circle_of_life_shm"
SEM_NAME = "/circle_of_life_sem"
TOTAL_SIZE = 4 + (POPULATION_LIMIT * 8) #1 byte type + 4 bytes energy + 3 bytes padding pre individual

class EnvState:
    def __init__(self, send_queue: MessageQueue, recv_queue: MessageQueue):
        # Configure parser and coms with display
        self.send_queue: MessageQueue = send_queue
        self.recv_queue: MessageQueue = recv_queue
        self.parser_thread: Thread = Thread(target=display_listener, args=(self,))
        self.parser_thread.start()
        
        # Configure thread to accept preys and predators
        self.socket_thread: Thread = Thread(target=socket_listener, args=(self,))
        self.socket_thread.start()
        
        # Configure preys and predators processes lists
        self.preys_processes: list[Process] = []
        self.predators_processes: list[Process] = []

        # 1. Create Shared Memory
        self.memory = posix_ipc.SharedMemory(SHM_NAME, posix_ipc.O_CREAT, size=TOTAL_SIZE)
        self.mapfile = mmap.mmap(self.memory.fd, self.memory.size)

        # 2. Create Semaphore (Mutex)
        self.sem = posix_ipc.Semaphore(SEM_NAME, posix_ipc.O_CREAT, initial_value=1)

        # 3. Initialize Grass (e.g., to 100)
        self.mapfile.seek(0)
        self.mapfile.write(struct.pack("i", GRASS_LIMIT))

        # 4. Manage IDs (Simple stack of free IDs)
        # IDs range from 0 to 99
        self.free_ids = list(range(POPULATION_LIMIT))

    def get_free_id(self) -> int | None:
        return self.free_ids.pop(0) if self.free_ids else None        


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
    
    if client_socket.recv(1024).decode().strip() in IndividualType:
        # If get_free_id() returns None, the individual will get it and terminate itself
        client_socket.send(f"{env.memory.name} {env.sem.name} {env.get_free_id()}".encode())

    client_socket.shutdown(SHUT_RDWR)
    client_socket.close()

def main():
    # Catch SIG_INT as display handles it. This file is not meant to be executed anyway, hence the shebang.
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # Connect to message queues created by display
    send_queue = MessageQueue("/env_recv", create=False)
    recv_queue = MessageQueue("/env_send", create=False)
    
    # TODO Add grass generation and rough periods

    env = EnvState(send_queue, recv_queue)
