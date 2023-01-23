#!/usr/bin/python3
"""Example for creating UCS packages."""

from datetime import datetime


if __name__ == "__main__":
    now = datetime.now()
    filename = "/tmp/testdeb-{:%y%m%d%H%M}".format(now)
    with open(filename, "a") as tmpfile:
        pass
