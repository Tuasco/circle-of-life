#!/usr/bin/env python3
from runtime import *

# Commands have the following pattern : (ACTION_TOKEN) (TARGET_TOKEN) [integer]
ACTION_TOKENS = ["add", "list", "delete"]
QUIT_TOKENS = ["quit", "exit", "stop"]
HELP_TOKENS = ["help", "?"]
TARGET_TOKENS = ["prey", "predator", "all", "gra"] #Not grass because of the strip("s")

# Functions corresponding to parsed words' positions
WORKERS = [
    [add_preys, add_predators, add_all, add_grass],
    [list_preys, list_predators, list_all, list_grass],
    [delete_preys, delete_predators, delete_all, delete_grass],
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