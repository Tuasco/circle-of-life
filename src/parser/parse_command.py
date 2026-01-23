#!/usr/bin/env python3
from execute_command import graceful_exit, display_help, execute_command_no_op

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

def parse_command(command: str):
    words = command.split(" ")
    worker_index = [0, 0]
    command_arg = 1

    for i, word in enumerate(words):
        word = word.lower()

        # If stop is given, do not go through the normal parsing pipeline, just exit
        if i == 0 and word in QUIT_TOKENS:
            graceful_exit()
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
    WORKERS[worker_index[0]][worker_index[1]](command_arg)

    return

def main(standalone_mode: bool = False):
    if standalone_mode:
        try:
            print("*** Honishell Ready - Parsing Command ***")
            while True:
                parse_command(input("> "))
        except KeyboardInterrupt, EOFError:
            graceful_exit(new_line=True)
            
        return
            
if __name__ == "__main__":
    main(standalone_mode=True)