#!/usr/bin/env python3
import mmap
import struct
from enum import Enum
from random import randint
from socket import socket, AF_INET, SOCK_STREAM
from time import sleep

import posix_ipc

MAX_ENERGY=100
GRASS_NUTRIENTS=15
MIN_ENERGY=0
HUNGER_THRESHOLD=50
SEX_THRESHOLD=70
MIN_WAIT=1
MAX_WAIT=10
MIN_ENERGY_LOSS=2
MAX_ENERGY_LOSS=10

# I'm unhappy that these two fuckers are duplicates from env_manager.py. They should be centralized!
LISTEN_ADDRESS = "127.0.0.1"
LISTEN_PORT = 15789

class IndividualType(Enum):
    PREY = "prey"
    PREDATOR = "predator"

class Individual:
    def __init__(self, individual_type: IndividualType):
        self.individual_type: IndividualType = individual_type
        self.energy: int = 100
        
        
def join_simulation(individual_type: IndividualType, verbose: bool = False) -> tuple[str, ...] | None:
    try:
        with socket(AF_INET, SOCK_STREAM) as client_socket:
            client_socket.settimeout(10)
            client_socket.connect((LISTEN_ADDRESS, LISTEN_PORT))
            client_socket.send(bytes(individual_type.value, "utf-8"))
            return tuple(client_socket.recv(1024).decode().strip().split())

    except ConnectionRefusedError:
        if verbose:
            print("Could not connect to simulation server")
        return None
    except TimeoutError:
        if verbose:
            print("Connection timeout")
        return None
    except OSError as e:
        if verbose:
            print(f"Connection error: {e}")
        return None

def main(individual_type: IndividualType, individual_id: int, verbose: bool = False):
    individual = Individual(individual_type)

    # Join the simulation over TCP and get shared memories
    mem, sem = join_simulation(individual_type, verbose)
    
    # Error or individual_id is None (no slots left)
    if None in [mem, sem, individual_id]:
        return

    # Attach to existing resources
    memory = posix_ipc.SharedMemory(mem)
    sem = posix_ipc.Semaphore(sem)
    mapfile = mmap.mmap(memory.fd, memory.size)

    # Calculate physical address in memory
    my_offset = 4 + (individual_id * 8)

    # Initialize in shared memory (Set Type and Starting Energy)
    type_code = 1 if individual_type.value == "prey" else 2
    with sem:
        mapfile.seek(my_offset)
        # Pack: B=unsigned char (type), i=integer (energy), 3x=padding
        mapfile.write(struct.pack("=Bi3x", type_code, MAX_ENERGY))

    while True:        
        # By not wrapping everything by the semaphore, we could run into a TOCTOU bug.
        # Even if we do, it isn't that critical. No one else SHOULD modify our values anyway.
        current_energy = 0
        with sem:
            mapfile.seek(my_offset + 1)
            current_energy = struct.unpack("=i", mapfile.read(4))[0]
                    
        individual.energy = current_energy - randint(MIN_ENERGY_LOSS, MAX_ENERGY_LOSS)
        if individual.energy <= 0:
            # Mark as dead in shared memory (type_code 0)
            with sem:
                mapfile.seek(my_offset)
                mapfile.write(struct.pack("=Bi3x", 0, 0))
            
            if verbose:
                print(f"We just died :(")
            break
            
        mapfile.seek(my_offset + 1)
        mapfile.write(struct.pack("i", individual.energy))
        
        # Finally, wait until the next update
        sleep(randint(MIN_WAIT, MAX_WAIT))


if __name__ == "__main__":
    main(IndividualType.PREY, verbose=True)