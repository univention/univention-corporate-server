#!/usr/bin/python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser

from ucsschool.lib.models.group import ComputerRoom
from univention.admin import uldap
from univention.udm import UDM


def create_room(
    lo: uldap.getAdminConnection,
    name: str,
    school: str,
    hosts: list,
) -> None:
    obj = ComputerRoom(name=f"{school}-{name}", school=school, hosts=hosts)
    result = obj.create(lo)
    assert result, f"create returned {result} for {obj}"


def main():

    desc = "create computer rooms for available windows hosts"
    parser = ArgumentParser(description=desc)
    parser.add_argument("school", type=str, help="school")
    args = parser.parse_args()

    lo = uldap.getAdminConnection()[0]
    udm = UDM(lo, 2)
    computers_windows = udm.get("computers/windows")
    all_hosts = [host.dn for host in computers_windows.search()]

    # room for all hosts
    create_room(lo, "all-windows-hosts", args.school, all_hosts)

    # create rooms with computers_in_room hosts
    computers_in_room = 5
    chunked_host_list = [
        all_hosts[i: i + computers_in_room]
        for i in range(0, len(all_hosts), computers_in_room)
    ]
    for room, hosts in enumerate(chunked_host_list):
        create_room(lo, f"room{room}", args.school, hosts)


if __name__ == "__main__":
    main()
