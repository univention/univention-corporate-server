#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: test log file permissions after logrotate
## exposure: dangerous
## tags: [udm]
## packages:
##   - univention-base-files

import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest


@dataclass
class FilePermissions:
    uid: int
    gid: int
    mode: int

    def __str__(self):
        return f"FilePermissions(uid={self.uid}, gid={self.gid}, mode={oct(stat.S_IMODE(self.mode))})"


def get_log_file_permissions(log_directory: Path) -> dict[Path, FilePermissions]:
    """
    Collects file permissions for all .log files in a directory tree.
    A dummy entry is written to empty log files to force logrotate to rotate.
    """
    permissions: dict[Path, FilePermissions] = {}
    for filepath in log_directory.rglob("*.log"):
        if filepath.is_file():
            try:
                file_stat = filepath.stat()
                permissions[filepath] = FilePermissions(
                    file_stat.st_uid, file_stat.st_gid, file_stat.st_mode,
                )

                if file_stat.st_size == 0:
                    try:
                        with open(filepath, "a") as fd:
                            fd.write("### DUMMY ENTRY FROM UCS TEST ###\n")
                    except OSError as e:
                        print(f"Warning: Could not write to empty log file {filepath}: {e}")
                    except Exception as e:
                        print(f"Warning: Unexpected error when writing to log file {filepath}: {e}")

            except FileNotFoundError:
                print(f"Warning: Log file {filepath} not found (possibly deleted).")
            except PermissionError:
                print(f"Warning: No authorization to read stat information for {filepath}.")
            except Exception as e:
                print(f"Error when retrieving the file statistics for {filepath}: {e}")
    return permissions


def compare_file_permissions(
    old_permissions: dict[Path, FilePermissions], new_permissions: dict[Path, FilePermissions],
) -> list[tuple[Path, FilePermissions, FilePermissions | None]]:
    "Compares two sets of file permissions and identifies differences."
    differences: list[tuple[Path, FilePermissions, FilePermissions | None]] = []

    # Check whether permissions have changed or new files have been added
    for filepath, new_perms in new_permissions.items():
        if filepath in old_permissions:
            if old_permissions[filepath] != new_perms:
                differences.append((filepath, old_permissions[filepath], new_perms))

    # Check whether files are missing after logrotate
    for filepath, old_perms in old_permissions.items():
        if filepath not in new_permissions:
            differences.append((filepath, old_perms, None))

    return differences


def test_log_permissions_after_logrotate():
    "Tests the file permissions of log files after executing logrotate."
    log_dir = Path("/var/log")

    old_log_permissions = get_log_file_permissions(log_dir)

    try:
        subprocess.check_call(["logrotate", "-f", "/etc/logrotate.conf"])
    except subprocess.CalledProcessError as e:
        pytest.fail(f"logrotate failed with exit code {e.returncode}: {e.stderr.decode()}")
    except FileNotFoundError:
        pytest.fail("The logrotate command was not found.")

    new_log_permissions = get_log_file_permissions(log_dir)
    differences = compare_file_permissions(old_log_permissions, new_log_permissions)

    if differences:
        print("\nERROR: Differences found:")
        for fn, old, new in differences:
            print(
                f'- File: {fn}\n  Old permissions: {old}\n  New permissions: {new or "FILE MISSING"}',
            )
        pytest.fail(f"There were {len(differences)} differences found in the log file permissions.")
