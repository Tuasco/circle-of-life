#!/usr/bin/env python3

def execute_command_no_op():
    print("execute_command_no_op")

def graceful_exit(new_line: bool = False):
    print("{}Exiting...".format('\n' if new_line else ''))
    exit()