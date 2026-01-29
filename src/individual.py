#!/usr/bin/env python3
import mmap
import struct
from enum import Enum
from random import randint
from socket import socket, AF_INET, SOCK_STREAM
from time import sleep

import posix_ipc

from CONSTS import *

MAX_ENERGY = 100
GRASS_NUTRIENTS = 20
PREY_NUTRIENTS = 50
MIN_ENERGY = 0
HUNGER_THRESHOLD = 50
SEX_THRESHOLD = 80
SEX_CHANCE = 5
MIN_WAIT = 2
MAX_WAIT = 8
PREY_MIN_ENERGY_LOSS = 1
PREY_MAX_ENERGY_LOSS = 8
PREDATOR_MIN_ENERGY_LOSS = 1
PREDATOR_MAX_ENERGY_LOSS = 3

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
        
        
def eat(individual: Individual, mapfile, sem, offset) -> int:
    if individual.individual_type == IndividualType.PREY:
        with sem:
            mapfile.seek(1)
            current_grass = struct.unpack("=i", mapfile.read(4))[0]
            
            if current_grass <= 0:
                return individual.energy
            
            # Remove a grass
            mapfile.seek(1)
            mapfile.write(struct.pack("i", current_grass - 1))
            
            # Update energy
            mapfile.seek(offset + 1)
            mapfile.write(struct.pack("i", individual.energy + GRASS_NUTRIENTS))
            
        return individual.energy + GRASS_NUTRIENTS
    else:
        with sem:
            # If an event happened but hasn't been processed by env, don't eat
            mapfile.seek(0)
            if struct.unpack("=B", mapfile.read(1))[0] != 0:
                return individual.energy

            mapfile.seek(offset + 1)
            
            for i in range(POPULATION_LIMIT):
                # Move the cursor to position and read
                mapfile.seek(5 + (i * 8))
                data = mapfile.read(8)
                type_code, energy = struct.unpack("=Bi3x", data)

                if type_code == 1 and energy < HUNGER_THRESHOLD and energy != 0:
                    mapfile.seek(5 + (i * 8))
                    mapfile.write(struct.pack("B", 0))
                    
                    mapfile.seek(0)
                    mapfile.write(struct.pack("B", 1))
                    
                    return individual.energy + PREY_NUTRIENTS
        
        return individual.energy
    
def reproduce():
    pass
        
        
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

    # Initialise in shared memory (Set Type and Starting Energy)
    my_offset = 5 + (individual_id * 8)
    type_code = 1 if individual_type == IndividualType.PREY else 2
    with sem:
        mapfile.seek(my_offset)
        # Pack: B=unsigned char (type), i=integer (energy), 3x=padding
        mapfile.write(struct.pack("=Bi3x", type_code, MAX_ENERGY))

    while True:        
        # By not wrapping everything by the semaphore, we could run into a TOCTOU bug.
        # Even if we do, it isn't that critical.
        current_energy = 0
        with sem:
            mapfile.seek(my_offset + 1)
            current_energy = struct.unpack("=i", mapfile.read(4))[0]
        
        if individual_type == IndividualType.PREY:
            current_energy -= randint(PREY_MIN_ENERGY_LOSS, PREY_MAX_ENERGY_LOSS)
        else:
            current_energy -= randint(PREDATOR_MIN_ENERGY_LOSS, PREDATOR_MAX_ENERGY_LOSS)
        
        # Handle death
        if current_energy <= 0:
            # Mark as dead in shared memory
            with sem:
                mapfile.seek(0)
                mapfile.write(struct.pack("B", 1))
                mapfile.seek(my_offset)
                mapfile.write(struct.pack("Bi3x", 0, 0))
            
            if verbose:
                print(f"We just died :(")
            break
            
        # Reproduce if horny
        if current_energy > SEX_THRESHOLD and randint(1, 100) <= 5:
            reproduce()
            
        # Eat if hungry
        if current_energy <= HUNGER_THRESHOLD:
            individual.energy = current_energy
            current_energy = eat(individual, mapfile, sem, my_offset)
            
        # Write new energy value
        with sem:
            mapfile.seek(my_offset + 1)
            mapfile.write(struct.pack("i", current_energy))
        individual.energy = current_energy
        
        # Finally, wait until the next update
        sleep(randint(MIN_WAIT, MAX_WAIT))


if __name__ == "__main__":
    main(IndividualType.PREY, verbose=True)