#!/usr/bin/env false
import struct
import sys
from multiprocessing import Process

from individual import IndividualType, main as individual_main


def add_preys(arg: int, env):
    added: int = 0

    for _ in range(arg):
        # Get id that will be the same in the shared mem and our dicts
        individual_id = env.get_free_id()

        if individual_id is None:
            print("Cannot add more individuals")
            break

        added += 1
        process = Process(target=individual_main, args=(IndividualType.PREY, individual_id))
        env.preys_processes[individual_id] = process
        process.start()

    print(f"{added} prey(s) added")

def add_predators(arg: int, env):
    added: int = 0

    for _ in range(arg):
        # Get id that will be the same in the shared mem and our dicts
        individual_id = env.get_free_id()

        if individual_id is None:
            print("Cannot add more individuals")
            break

        added += 1
        process = Process(target=individual_main, args=(IndividualType.PREDATOR, individual_id))
        env.predators_processes[individual_id] = process
        process.start()

    print(f"{added} predator(s) added")
    
def add_all(arg: int, env):
    add_preys(arg, env)
    add_predators(arg, env)
    
def add_grass(arg: int, env):
    with env.sem:
        env.mapfile.seek(0)
        current_grass = struct.unpack("=i", env.mapfile.read(4))[0]
        env.mapfile.seek(0)
        env.mapfile.write(struct.pack("i", current_grass + arg))


def list_preys(_, env):
    print("Preys in the simulation (Shared Memory View):")
    count = 0

    with env.sem:
        for i in range(env.population_limit):
            # Move the cursor to position and read
            env.mapfile.seek(4 + (i * 8))
            data = env.mapfile.read(8)
            type_code, energy = struct.unpack("=Bi3x", data)

            if type_code == 1 and energy > 0:
                print(f" - ID {i}: Energy {energy}")
                count += 1

    if count == 0:
        print("No active preys found in shared memory.")
    else:
        print(f"Total: {count} prey(s).")

def list_predators(_, env):
    print("Predators in the simulation (Shared Memory View):")
    count = 0

    with env.sem:
        for i in range(env.population_limit):
            # Move the cursor to position and read
            env.mapfile.seek(4 + (i * 8))
            data = env.mapfile.read(8)
            type_code, energy = struct.unpack("=Bi3x", data)

            if type_code == 2 and energy > 0:
                print(f" - ID {i}: Energy {energy}")
                count += 1

    if count == 0:
        print("No active predators found in shared memory.")
    else:
        print(f"Total: {count} predator(s).")
        
def list_all(_, env):
    list_preys(None, env)
    print()
    list_predators(None, env)

def list_grass(_, env):
    current_grass = 0
    with env.sem:
        env.mapfile.seek(0)
        current_grass = struct.unpack("=i", env.mapfile.read(4))[0]
        
    print(f"Total: {current_grass} grass")


def _delete_individuals(env, processes_dict, count_to_delete, label):
    """Helper to remove N individuals from a specific dictionary."""
    if not processes_dict:
        print(f"No {label}s to delete.")
        return


    # Get a list of IDs currently in the dictionary
    target_ids = list(processes_dict.keys())[:count_to_delete]

    deleted_count = 0
    for slot_id in target_ids:
        # Stop the process
        proc = processes_dict.pop(slot_id)
        if proc.is_alive():
            proc.terminate()
            proc.join()

        # Clean the Shared Memory
        offset = 4 + (slot_id * 8)
        with env.sem:
            env.mapfile.seek(offset)
            env.mapfile.write(b'\x00' * 8)

        # Return the ID to the pool
        env.return_id(slot_id)
        deleted_count += 1

    print(f"Removed {deleted_count} {label}(s).")

def delete_preys(arg: int, env):
    _delete_individuals(env, env.preys_processes, arg, IndividualType.PREY.value)

def delete_predators(arg: int, env):
    _delete_individuals(env, env.predators_processes, arg, IndividualType.PREDATOR.value)
    
def delete_all(arg: int, env):
    delete_preys(arg, env)
    delete_predators(arg, env)

def delete_grass(arg: int, env):
    current_grass = 0
    with env.sem:
        env.mapfile.seek(0)
        current_grass = struct.unpack("=i", env.mapfile.read(4))[0]
        env.mapfile.seek(0)
        env.mapfile.write(struct.pack("i", min(0, current_grass - arg)))

    print(f"Removed {min(arg, current_grass)} grass.")


def graceful_exit(env, new_line: bool = False):
    print("{}Exiting...".format('\n' if new_line else ''))

    # Stop threads
    env.socket_thread.join(timeout=0)
    env.grass_thread.join(timeout=0)

    # Clear preys and predators processes
    # This could be improved by joining them in parallel
    for proc in env.predators_processes.values():
        proc: Process
        proc.terminate()
        proc.join()
        proc.close()

    for proc in env.preys_processes.values():
        proc: Process
        proc.terminate()
        proc.join()
        proc.close()

    env.mapfile.close()
    env.memory.unlink()
    env.sem.unlink()
    del env.drought_lock
    env.send_queue.send("quit".encode("utf-8"))
    env.send_queue.close()
    env.recv_queue.close()

    sys.exit(0)


def display_help():
    print("""
Simulation Interpreter Help:
Commands format: ACTION TARGET [NUMBER]

ACTIONS:
- add: Add NUMBER instances of TARGET to the simulation
- list: List all current TARGET instances
- delete: Remove NUMBER instances of TARGET from the simulation
- stop: Stop the simulation and exit

TARGETS:
- prey: Simulation prey entities
- predator: Simulation predator entities
- all: Prey and predator entities (prey is operated on first)
- grass: Simulation grass entities

EXAMPLES:
- add prey 5      : Add 5 prey
- add all 2       : Add 2 prey and 2 predators
- add grass 12    : Add 12 grass (regardless of the limit)
- list predator   : Show all predators
- delete prey 2   : Remove 2 prey
- stop            : Exit simulation
- help            : Show this help
- ?               : Show this help

NUMBER is optional. For add/delete; defaults to 1. For list; ignored.
""")