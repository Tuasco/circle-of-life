#!/usr/bin/env python3
from enum import Enum
from time import sleep


class IndividualType(Enum):
    PREY = "prey"
    PREDATOR = "predator"


def main(individual_type: IndividualType):
    while True:
        sleep(10)
