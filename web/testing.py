#!/usr/bin/env python
import os
import sys


if __name__ == "__main__":

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config")
    os.environ.setdefault("DJANGO_CONFIGURATION", "Testing")

    from configurations.management import execute_from_command_line
    execute_from_command_line(sys.argv)
