#!/usr/bin/python3

"""
Change docker compose main service image to given image.
Run this script after "univention-app update" and before
"univention-install".
"""

import argparse

import yaml

from univention.appcenter.app_cache import Apps
from univention.appcenter.ucr import ucr_run_filter


def change_app_compose_image(args: argparse.ArgumentParser,) -> None:
    apps_cache = Apps()
    candidate = apps_cache.find(args.app, latest=True,)
    compose_file = candidate.get_cache_file("compose")
    compose = yaml.safe_load(ucr_run_filter(open(compose_file).read()))
    current_image = compose["services"][candidate.docker_main_service]["image"]
    new_compose = []
    found = False
    for line in open(compose_file):
        if current_image in line:
            line = line.replace(current_image, args.image,)
            found = True
        new_compose.append(line)
    if not found:
        raise Exception(f"Could not replace image {current_image} with {args.image} in {compose_file}")
    with open(compose_file, "w",) as fd:
        [fd.write(line) for line in new_compose]
    print(f"changed {compose_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Change docker compose main service image to given image")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-a", "--app", required=True, help="app id",)
    parser.add_argument("-i", "--image", required=True, help="the new image for the main service of the app",)
    args = parser.parse_args()
    change_app_compose_image(args)
