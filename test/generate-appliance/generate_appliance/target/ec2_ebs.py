# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

from __future__ import annotations
import datetime
import sys
from logging import getLogger
from math import ceil
from time import sleep
from typing import TYPE_CHECKING

import boto3

from ..files.raw import Raw
from ..files.vmdk import Vmdk
from . import Target


if TYPE_CHECKING:
    from mypy_boto3_ec2 import EC2Client
    from mypy_boto3_s3 import S3Client

log = getLogger(__name__)


class Progress:
    def __init__(self, path: str, size: int) -> None:
        self.path = path
        self.size = size
        self.seen = 0

    def __call__(self, amount: int) -> None:
        self.seen += amount
        percent = 100 * self.seen // self.size
        sys.stdout.write("\r%s  %s / %s  (%d%%)" % (self.path, self.seen, self.size, percent))
        sys.stdout.flush()


class EC2_EBS(Target):
    """Amazon AWS EC2 AMI (EBS based) (HVM x64_64)"""

    default = False
    tag = False
    public = False

    def create(self, image: Raw) -> None:
        vmdk = Vmdk(image)

        s3 = boto3.client("s3", region_name=self.options.region)
        vmdk_get = self.upload_file(s3, vmdk, self.options.bucket)

        ec2 = boto3.client("ec2", region_name=self.options.region)
        import_task_id = self.import_snapshot(ec2, vmdk_get)
        snapshot_id = self.wait_for_snapshot(ec2, import_task_id)
        ami = self.register_image(ec2, snapshot_id, size=ceil(vmdk.volume_size() / 1e9))
        print(f'Generated "{self}" appliance as\n  {ami}')

        if self.tag:
            self.add_tag(ec2, ami)

        if self.public:
            self.make_public(ec2, ami)

    def upload_file(self, s3: S3Client, vmdk: Vmdk, bucket: str) -> str:
        image_name = self.machine_name + ".vmdk"
        # <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/upload_file.html>
        s3.upload_file(
            vmdk.path().as_posix(),
            bucket,
            image_name,
            ExtraArgs={
                "ACL": "aws-exec-read",
                "Expires": datetime.datetime.now() + datetime.timedelta(days=1),
                "StorageClass": "REDUCED_REDUNDANCY",
            },
            Callback=Progress(vmdk.path().as_posix(), vmdk.file_size()),
        )
        vmdk_get = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': bucket,
                "Key": image_name,
            },
            ExpiresIn=3600,
            HttpMethod="GET",
        )
        return vmdk_get

    def import_snapshot(self, ec2: EC2Client, vmdk_get: str) -> str:
        # <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/import_snapshot.html>
        response = ec2.import_snapshot(
            Description=self.machine_name,
            DiskContainer={
                "Description": self.machine_name,
                "Format": "VMDK",
                # "UserBucket": {
                #     "S3Bucket": options.region,
                #     "S3Key": manifest_name,
                # },
                "Url": vmdk_get,
            },
            DryRun=False,
            # Encrypted=False,
        )
        log.debug("import_snapshot: %r", response)
        import_task_id = response["ImportTaskId"]
        return import_task_id

    @staticmethod
    def wait_for_snapshot(ec2: EC2Client, import_task_id: str) -> str:
        try:
            # <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/get_waiter.html>
            # <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/waiter/SnapshotImported.html>
            waiter = ec2.get_waiter('snapshot_imported')  # 1.26.69+
            waiter.wait(
                ImportTaskIds=[import_task_id],
                WaiterConfig={
                    'Delay': 15,
                    'MaxAttempts': 100,
                },
            )
            count = 1
        except ValueError:
            count = 1000

        for _ in range(count):
            # <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_import_snapshot_tasks.html>
            response = ec2.describe_import_snapshot_tasks(ImportTaskIds=[import_task_id])
            log.debug("describe_import_snapshot_tasks: %r", response)
            detail = response["ImportSnapshotTasks"][0]["SnapshotTaskDetail"]
            status = detail["Status"]
            if status == "completed":
                return detail["SnapshotId"]
            if status == "active":
                progress = int(detail["Progress"])
                Progress(import_task_id, 100)(progress)
            else:
                print(detail)
            sleep(15)

        raise ValueError("Import failed")

    def register_image(self, ec2: EC2Client, snapshot_id: str, size: int) -> str:
        # <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/register_image.html>
        response = ec2.register_image(
            Architecture="x86_64",
            BlockDeviceMappings=[
                {
                    "DeviceName": "/dev/xvda",
                    "Ebs": {
                        "DeleteOnTermination": True,
                        "SnapshotId": snapshot_id,
                        "VolumeSize": size,  # GiB
                        "VolumeType": "gp2",
                    },
                },
            ],
            Description="https://www.univention.com/",
            Name=self.machine_name,
            DryRun=False,
            EnaSupport=True,
            RootDeviceName="/dev/xvda",
            VirtualizationType="hvm",
            # BootMode="legacy-bios",
        )
        log.debug("register_image: %r", response)
        ami = response["ImageId"]
        return ami

    def add_tag(self, ec2: EC2Client, ami: str) -> None:
        # <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/create_tags.html>
        ec2.create_tags(
            Resources=[
                ami,
            ],
            Tags=[
                {
                    "Key": "Name",
                    "Value": self.machine_name,
                },
            ],
        )

    @staticmethod
    def make_public(ec2: EC2Client, ami: str) -> None:
        # <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/modify_image_attribute.html>
        response = ec2.modify_image_attribute(
            ImageId=ami,
            LaunchPermission={
                "Add": [
                    {
                        "Group": "all",
                    },
                ],
            },
        )
        log.debug("modify_image_attribute: %r", response)
