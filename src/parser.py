#!/usr/bin/env python3
import sys

def execute_command_no_op(arg: int, env):
    print("execute_command_no_op with argument {}".format(arg))

def graceful_exit(env, new_line: bool = False):
    print("{}Exiting...".format('\n' if new_line else ''))
    
    # Stop env
    env.send_queue.put("quit")
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

EXAMPLES:
- add prey 5      : Add 5 prey
- list predator   : Show all predators
- delete prey 2   : Remove 2 prey
- stop            : Exit simulation
- help            : Show this help
- ?               : Show this help

NUMBER is optional for add/delete; defaults to 1.
""")

# Commands have the following pattern : (ACTION_TOKEN) (TARGET_TOKEN) [integer]
ACTION_TOKENS = ["add", "list", "delete"]
QUIT_TOKENS = ["quit", "exit", "stop"]
HELP_TOKENS = ["help", "?"]
TARGET_TOKENS = ["prey", "predator"]

# Functions corresponding to parsed words' positions
WORKERS = [
    [execute_command_no_op, execute_command_no_op],
    [execute_command_no_op, execute_command_no_op],
    [execute_command_no_op, execute_command_no_op],
]

def parse_command(command: str, env):
    words = command.split(" ")
    worker_index = [0, 0]
    command_arg = 1

    for i, word in enumerate(words):
        word = word.lower()

        # If stop is given, do not go through the normal parsing pipeline, just exit
        if i == 0 and word in QUIT_TOKENS:
            graceful_exit(env)
            return
        
        # If help is given, do not go through normal parsing pipeline, display help only
        if i == 0 and word in HELP_TOKENS:
            display_help()
            return

        # The first word must be an action token
        if i == 0 and word not in ACTION_TOKENS:
            print(f"***Action token expected, got {word}")
            return

        # The second word must be a target token
        if i == 1 and word.strip('s') not in TARGET_TOKENS:
            print(f"***Target token expected, got {word}")
            return

        # The third word must be a positive integer
        if i == 2 and not word.isdigit():
            print(f"***Integer expected, got {word}")
            return

        # Only three words are accepted
        if i >= 3:
            print("***3 words expected, got more")
            return

        # Checks are done, syntax is correct from now on
        if i == 0:
            worker_index[0] = ACTION_TOKENS.index(word)
            continue

        if i == 1:
            worker_index[1] = TARGET_TOKENS.index(word.strip('s'))
            continue

        if i == 2:
            command_arg = int(word)  # Should work, already verified that it is a string
            break  # Not necessary, should be the last word anyway

    # Execute parsed command
    WORKERS[worker_index[0]][worker_index[1]](command_arg, env)
    return

def main(env):
    try:
        print("*** Honishell Ready - Parsing Command ***")
        while True:
            parse_command(input("> "), env)
    except KeyboardInterrupt, EOFError:
        graceful_exit(env, new_line=True)