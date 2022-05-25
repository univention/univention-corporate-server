#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import sys
from configparser import ConfigParser

template_file = "scenarios/veyon/veyon.cfg"


def main():
    desc = "start veyon test with configurable amount of windows clients"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "-w",
        "--windows-clients",
        default=1,
        type=int,
        help="number of windows clients",
    )
    parser.add_argument(
        "-v",
        "--virtualization",
        choices=["kvm", "ec2"],
        default="ec2",
    )
    args = parser.parse_args()

    max_windows_hosts = 25
    if args.virtualization == "kvm":
        max_windows_hosts = 5
    if args.windows_clients > max_windows_hosts:
        parser.error(
            "{} windows clients, this seems excessive, aborting!".format(args.windows_clients)
        )
    config = ConfigParser(interpolation=None)
    config.read(template_file)

    # copy windows section
    windows_section = list(config.items("windows"))

    # add additional windows sections
    ip_list = "[windows_IP] "
    section = ""
    for i in range(2, args.windows_clients + 1):
        section = "windows{}".format(i)
        ip_list += "[{}_IP] ".format(section)
        config.add_section(section)
        for option, value in windows_section:
            config.set(section, option, value)

    # add windows hosts to global environment
    environment = config.get("Global", "environment")
    new_environment = ""
    for env in environment.split("\n"):
        if env.startswith("UCS_ENV_WINDOWS_CLIENTS="):
            continue
        new_environment += "{}\n".format(env)
    new_environment += "UCS_ENV_WINDOWS_CLIENTS={}\n".format(ip_list)
    config.set("Global", "environment", new_environment)

    config.write(sys.stdout)


if __name__ == "__main__":
    main()
