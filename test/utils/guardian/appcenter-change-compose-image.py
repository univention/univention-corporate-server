#!/usr/bin/python3
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Change docker compose main service image to given image.
Run this script after "univention-app update" and before
"univention-install".
"""

import argparse
import re

import yaml

from univention.appcenter.app_cache import Apps
from univention.appcenter.ucr import ucr_run_filter


def change_app_compose_image(args: argparse.ArgumentParser) -> None:

    apps_cache = Apps()
    candidate = apps_cache.find(args.app, latest=True)
    compose_file = candidate.get_cache_file("compose")

    with open(compose_file) as f:
        raw_file_content = f.read()
        compose = yaml.safe_load(ucr_run_filter(raw_file_content))

    missing_images = []

    current_image = compose["services"][candidate.docker_main_service]["image"]

    if current_image not in raw_file_content:
        missing_images.append(current_image)

    new_file_content = re.sub(rf"(\n\s*)image: {current_image}(\n*)", rf"\1image: {args.image}\2", raw_file_content)

    if args.other_service:
        for service_name, image in args.other_service:
            try:
                current_image = compose["services"][service_name]["image"]
            except KeyError as e:
                raise Exception(f"Service {service_name} not found in compose file.") from e
            if current_image not in new_file_content:
                missing_images.append(current_image)
            new_file_content = re.sub(rf"(\n\s*)image: {current_image}(\n\s*)", rf"\1image: {image}\2", new_file_content)

    if missing_images:
        raise Exception(f"Cannot find the following images in {compose_file}: " + ",".join(missing_images))

    with open(compose_file, "w") as fd:
        fd.write(new_file_content)

    print(f"changed {compose_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Change docker compose main service image to given image")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-a", "--app", required=True, help="app id")
    parser.add_argument("-i", "--image", required=True, help="the new image for the main service of the app")
    parser.add_argument("-o", "--other_service", nargs=2, action="append", metavar=("service", "image"), required=False, help="images for other services")
    args = parser.parse_args()
    change_app_compose_image(args)
