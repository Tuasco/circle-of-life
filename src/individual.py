#!/usr/bin/env python3
from enum import Enum
from time import sleep
from socket import socket, AF_INET, SOCK_STREAM

MAX_ENERGY=100
MIN_ENERGY=0
HUNGER_THRESHOLD=50
SEX_THRESHOLD=70
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
        

def main(individual_type: IndividualType, verbose: bool = False):
    individual = Individual(individual_type)

    # Join the simulation
    try:
        with socket(AF_INET, SOCK_STREAM) as client_socket:
            client_socket.settimeout(10)
            client_socket.connect((LISTEN_ADDRESS, LISTEN_PORT))
            client_socket.send(bytes(individual.individual_type.value, "utf-8"))

            response = client_socket.recv(1024)
            if verbose:
                print(f"Server response: {response.decode('utf-8')}")

    except ConnectionRefusedError:
        if verbose:
            print("Could not connect to simulation server")
        return
    except TimeoutError:
        if verbose:
            print("Connection timeout")
        return
    except OSError as e:
        if verbose:
            print(f"Connection error: {e}")
        return

    while True:
        sleep(10)


if __name__ == "__main__":
    main(IndividualType.PREY, verbose=True)