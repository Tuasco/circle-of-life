#!/usr/bin/env python3
import sys

def execute_command_no_op(arg: int):
    print("execute_command_no_op with argument {}".format(arg))

def graceful_exit(new_line: bool = False):
    from os import _exit
    
    print("{}Exiting...".format('\n' if new_line else ''))
    try:
        sys.exit(0)
    except SystemExit:
        _exit(1)
    
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