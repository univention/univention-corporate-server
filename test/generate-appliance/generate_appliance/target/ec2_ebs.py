# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

import math
import sys
import time
import uuid
from argparse import Namespace  # noqa: F401
from typing import Iterator, cast  # noqa: F401

import boto
import boto.ec2
import lxml.builder
import lxml.etree

from ..files.raw import Raw  # noqa: F401
from ..files.vmdk import Vmdk
from . import Target


def log(text, newline=True):
    # type: (str, bool) -> None
    sys.stderr.write(text)
    if newline:
        sys.stderr.write('\n')
    sys.stderr.flush()


def create_import_manifest(image, vmdk, bucket, folder_name, image_name, volume_size, part_size, url_lifetime):
    # type: (Raw, Vmdk, boto.s3.bucket.Bucket, uuid.UUID, str, int, int, int) -> bytes
    # <http://docs.aws.amazon.com/AWSEC2/latest/APIReference/manifest.html>
    E = lxml.builder.ElementMaker()
    part_count = int(math.ceil(float(vmdk.file_size()) / part_size))
    parts = []
    for index, offset in enumerate(x * part_size for x in range(part_count)):
        key = boto.s3.key.Key(bucket, '%s/%s.part%d' % (folder_name, image_name, index))  # TODO: redundant code
        parts.append(
            E.part(
                # Complex type defining the starting and ending byte count of a part.
                E(
                    'byte-range',
                    # Offset of a part's first byte in the disk image.
                    start='%d' % (offset,),
                    # Offset of a part's last byte in the disk image.
                    end='%d' % (min(offset + part_size, vmdk.file_size()) - 1,),
                ),
                # The S3 object name of the part.
                E.key(key.name),
                # Signed URLs for issuing a HEAD request on the S3 object containing this part.
                E('head-url', key.generate_url(url_lifetime, 'HEAD')),
                # Signed URLs for issuing a GET request on the S3 object containing this part.
                E('get-url', key.generate_url(url_lifetime, 'GET')),
                # Signed URLs for issuing a DELETE request on the S3 object containing this part.
                E('delete-url', key.generate_url(url_lifetime, 'DELETE')),
                # Index number of this part.
                index='%d' % (index,),
            ),
        )
    manifest_key = boto.s3.key.Key(bucket, '%s/%smanifest.xml' % (folder_name, image_name))  # TODO: redundant code
    manifest = E.manifest(
        # Version designator for the manifest file,
        E.version('2010-11-15'),
        # File format of volume to be imported, with value RAW, VHD, or VMDK.
        E('file-format', 'VMDK'),
        # Complex type describing the software that created the manifest.
        E.importer(
            # Name of the software that created the manifest.
            E.name('generate_appliance'),
            # Version of the software that created the manifest.
            E.version('2.1'),
            # Release number of the software that created the manifest.
            E.release('1'),
        ),
        # Signed URL used to delete the stored manifest file.
        E('self-destruct-url', manifest_key.generate_url(url_lifetime, 'DELETE')),
        # Complex type describing the size and chunking of the volume file.
        E(
            'import',
            # Exact size of the file to be imported (bytes on disk).
            E.size('%d' % (vmdk.file_size(),)),
            # Rounded size in gigabytes of volume to be imported.
            # - assumed meaning: size of the volume in GiB, because EC2 EBS volumes are provisioned in GiB
            E('volume-size', '%d' % (volume_size,)),
            # Complex type describing and counting the parts into which the file is split.
            E.parts(
                # Definition of a particular part. Any number of parts may be defined.
                *parts,
                # Total count of the parts.
                count='%d' % (part_count,),
            ),
        ),
    )
    return cast(bytes, lxml.etree.tostring(manifest, encoding='UTF-8', xml_declaration=False, pretty_print=True))


def chunks(imagefile, chunksize):
    # type: (Vmdk, int) -> Iterator[bytes]
    handle = open(imagefile.path(), 'rb')
    while True:
        chunk = handle.read(chunksize)
        yield chunk
        if len(chunk) < chunksize:
            break


class EC2_EBS(Target):
    """Amazon AWS EC2 AMI (EBS based) (HVM x64_64)"""

    default = False

    def create(self, image, options):
        # type: (Raw, Namespace) -> None
        machine_name = options.product
        if options.version is not None:
            machine_name += ' ' + options.version
        image_name = '%s-disk1.vmdk' % (options.product,)
        part_size = 10 * 1000 * 1000  # 10 MB
        url_lifetime = 24 * 60 * 60  # 1 day

        volume_size = int(math.ceil(float(image.file_size()) / 1024 / 1024 / 1024))  # GiB
        folder_name = uuid.uuid4()
        s3 = boto.s3.connect_to_region(boto.connect_s3().get_bucket(options.bucket).get_location())  # type: ignore[no-untyped-call]
        ec2 = boto.ec2.connect_to_region(options.region)  # type: ignore[no-untyped-call]
        bucket = s3.get_bucket(options.bucket)
        vmdk = Vmdk(image)
        keys_to_delete = []
        manifest = create_import_manifest(image, vmdk, bucket, folder_name, image_name, volume_size, part_size, url_lifetime)

        log('Uploading manifest…')
        manifest_key = boto.s3.key.Key(bucket, '%s/%smanifest.xml' % (folder_name, image_name))  # TODO: redundant code
        manifest_key.storage_class = 'REDUCED_REDUNDANCY'
        manifest_key.set_contents_from_string(manifest)
        keys_to_delete.append(manifest_key)
        log('  OK')

        part_count = int(math.ceil(float(vmdk.file_size()) / part_size))
        for index, part in enumerate(chunks(vmdk, part_size)):
            log('Uploading part %d/%d…' % (index, part_count))
            key = boto.s3.key.Key(bucket, '%s/%s.part%d' % (folder_name, image_name, index))  # TODO: redundant code
            key.storage_class = 'REDUCED_REDUNDANCY'
            key.set_contents_from_string(part)
            keys_to_delete.append(key)
            log('  OK')

        log('Generating volume ', False)
        manifest_url = manifest_key.generate_url(url_lifetime, 'GET')
        zone = ec2.get_all_zones()[0]
        task = ec2.import_volume(
            volume_size,
            zone,
            description=machine_name,
            image_size=vmdk.file_size(),
            manifest_url=manifest_url,
        )
        # wait for volume
        while True:
            for task in ec2.get_all_conversion_tasks(task_ids=[task.id]):
                pass  # just fill <task> variable
            if task.state != 'active':
                log(' done')
                break
            time.sleep(32)  # TODO adaptive and jittery
            # TODO: abort if no progress after some time?
            log('.', False)
        if task.state == 'completed':
            log('  %s' % (task.volume_id,))
        else:
            log('  Failed (%r, %r, %r, %r)' % (task.id, task.bytes_converted, task.state, getattr(task, 'statusMessage', None)))

        for index, key in enumerate(keys_to_delete):
            log('Deleting part %d/%d… ' % (index, len(keys_to_delete)), False)
            if key.delete():
                log('OK')
            else:
                log('Failed')
        if task.state != 'completed':
            return  # abort

        log('Generating snapshot ', False)
        snapshot = ec2.create_snapshot(task.volume_id, description=machine_name)
        # wait for snapshot
        while True:
            snapshot.update()
            if snapshot.status != 'pending':
                log(' done')
                break
            time.sleep(32)  # TODO adaptive and jittery
            # TODO: abort if no progress after some time?
            log('.', False)
        if snapshot.status == 'completed':
            log('  %s' % (snapshot.id,))
        else:
            log('  Failed (%r, %r, %r, %r)' % (snapshot.id, snapshot.volume_id, snapshot.status, snapshot.progress))
            return  # abort
        if ec2.delete_volume(task.volume_id):
            log('Deleted volume %s' % (task.volume_id,))
        else:
            log('Could not delete volume %s' % (task.volume_id,))

        log('Generating image', False)
        ami_id = ec2.register_image(
            name=machine_name,
            description='%s' % (
                options.vendor_url,
            ),
            architecture='x86_64',
            root_device_name='/dev/xvda',
            virtualization_type='hvm',
            snapshot_id=snapshot.id,
        )
        # wait for image
        while True:
            amis = [ami for ami in ec2.get_all_images(image_ids=[ami_id]) if ami.state != 'pending']
            if amis:
                break
            time.sleep(32)  # TODO adaptive and jittery
            # TODO: abort if no progress after some time?
            log('.', False)
        log(' done')

        for ami in amis:
            if ami.state == 'available':
                log('Generated "%s" appliance as\n  %s' % (self, ami.id))
            else:
                log('Could not generate image (%r, %r, %r)' % (self, ami.id, ami.state))
