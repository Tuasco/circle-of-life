#!/usr/bin/env false
import mmap
import signal
import struct
from multiprocessing import Process, Lock
from random import randint
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, SHUT_RDWR
from threading import Thread
from time import sleep

import posix_ipc

from individual import IndividualType
from parser import parse_command

LISTEN_ADDRESS = "127.0.0.1"
LISTEN_PORT = 15789
LISTEN_LIMIT = 5

MIN_GRASS_WAIT = 1
MAX_GRASS_WAIT = 5
SHIT_HAPPENS_INTERVAL = 40
SHIT_HAPPENS_DURATION = 3

POPULATION_LIMIT = 10
GRASS_LIMIT = 4
SHM_NAME = "/circle_of_life_shm"
SEM_NAME = "/circle_of_life_sem"
TOTAL_SIZE = 4 + (POPULATION_LIMIT * 8) #1 byte type + 4 bytes energy + 3 bytes padding pre individual

class EnvState:
    def __init__(self, send_queue: posix_ipc.MessageQueue, recv_queue: posix_ipc.MessageQueue):
        # Configure parser and coms with display
        self.send_queue: posix_ipc.MessageQueue = send_queue
        self.recv_queue: posix_ipc.MessageQueue = recv_queue
        self.parser_thread: Thread = Thread(target=display_listener, args=(self,))
        self.parser_thread.start()
        
        # Configure thread to accept preys and predators
        self.socket_thread: Thread = Thread(target=socket_listener, args=(self,))
        self.socket_thread.start()
        self.preys_processes: dict[int, Process] = {}
        self.predators_processes: dict[int, Process] = {}

        # Create zero-filled shared memory
        self.memory = posix_ipc.SharedMemory(SHM_NAME, posix_ipc.O_CREAT, size=TOTAL_SIZE)
        self.mapfile = mmap.mmap(self.memory.fd, self.memory.size)
        self.mapfile.seek(0)
        self.mapfile.write(b'\x00' * TOTAL_SIZE)
        self.sem = posix_ipc.Semaphore(SEM_NAME, posix_ipc.O_CREAT, initial_value=1)
        # Initialise grass value
        self.mapfile.seek(0)
        self.mapfile.write(struct.pack("i", GRASS_LIMIT))
        # Simple stack of free IDs
        self.free_ids = list(range(POPULATION_LIMIT))
        self.population_limit = POPULATION_LIMIT #Needed for parser

        # Configure grass growth
        self.grass_thread = Thread(target=grass, args=(self,))
        self.grass_thread.start()
        # Configure drought episodes
        self.drought_lock = Lock()
        self.drought_remaining = 0
        signal.signal(signal.SIGALRM, self.handle_shit_happened)
        signal.setitimer(signal.ITIMER_REAL, SHIT_HAPPENS_INTERVAL, SHIT_HAPPENS_INTERVAL)

    def get_free_id(self) -> int | None:
        return self.free_ids.pop(0) if self.free_ids else None

    def return_id(self, returned_id: int):
        self.free_ids.append(returned_id)

    def handle_shit_happened(self, signum, frame):
        with self.drought_lock:
            self.drought_remaining = SHIT_HAPPENS_DURATION


def display_listener(env):
    while True:
        command, _ = env.recv_queue.receive()
        command = command.decode("utf-8")
        parse_command(command, env)
        env.send_queue.send('\0'.encode("utf-8"))

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
        # Send memory and semaphore names to the joined individual
        client_socket.send(f"{env.memory.name} {env.sem.name}".encode())

    client_socket.shutdown(SHUT_RDWR)
    client_socket.close()


def grass(env: EnvState):
    while True:
        sleep(randint(MIN_GRASS_WAIT, MAX_GRASS_WAIT))
        
        # Check if a drought episode is occuring
        # Aquiring the lock before reading would prevent a TOCTOU, but it wouldn't be an issue regardless
        if env.drought_remaining > 0:
            with env.drought_lock:
                env.drought_remaining -= 1
            continue
        
        # Add one grass (stonks)
        current_grass = 0
        with env.sem:
            env.mapfile.seek(0)
            current_grass = struct.unpack("=i", env.mapfile.read(4))[0]
            
            if current_grass < GRASS_LIMIT:
                env.mapfile.seek(0)
                env.mapfile.write(struct.pack("i", current_grass + 1))
        
    return

def main():
    # Catch SIG_INT as display handles it. This file is not meant to be executed anyway, hence the shebang.
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # Connect to message queues created by display
    send_queue = posix_ipc.MessageQueue("/env_recv")
    recv_queue = posix_ipc.MessageQueue("/env_send")
    
    # TODO Add grass generation and rough periods

    env = EnvState(send_queue, recv_queue)
