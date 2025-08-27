#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""REST API endpoint for manual recycle bin purging."""

import asyncio
import json
import os

import tornado.web
from tornado.web import HTTPError


CLEANUP_SCRIPT_PATH = '/usr/share/univention-directory-manager-tools/univention-recycle-bin-clean-expired-entries'


class RecycleBinPurge(tornado.web.RequestHandler):
    """Manually purge specific recycle bin entries."""

    async def post(self):
        """
        Handle POST request to purge recycle bin entries.

        Expects JSON body with 'dns' field containing list of DNs to purge.
        Returns structured JSON response with success/error details.

        :raises HTTPError: For invalid requests or processing errors
        """
        try:
            body = json.loads(self.request.body)
        except (json.JSONDecodeError, TypeError):
            raise HTTPError(400, "Invalid JSON body")

        if 'dns' not in body:
            raise HTTPError(400, "Missing 'dns' field in request body")

        dns = body.get('dns', [])
        if not isinstance(dns, list):
            raise HTTPError(400, "'dns' must be a list")

        if not dns:
            raise HTTPError(400, "'dns' list cannot be empty")

        user_dn = "Administrator"

        for dn in dns:
            if not isinstance(dn, str):
                raise HTTPError(400, "All DNs must be strings")
            if '=' not in dn or any(c in dn for c in ['$', '`', '\n', '\r', ';', '|', '&']):
                raise HTTPError(400, f"Invalid DN format: {dn}")

        dns_input = '\n'.join(dns)

        cmd = [
            "python3",
            CLEANUP_SCRIPT_PATH,
            "--remove-expired",
            "--purge-dns-stdin",
            "--json-output",
        ]

        try:
            env = os.environ.copy()
            env['MANUAL_ACTOR_DN'] = user_dn

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=dns_input.encode()),
                    timeout=30,
                )
            except TimeoutError:
                proc.kill()
                await proc.wait()
                self.set_status(504)
                self.set_header("Content-Type", "application/json")
                self.write(json.dumps({
                    "error_id": "TIMEOUT",
                    "message": "Purge operation timed out after 30 seconds",
                    "affected_items": dns,
                }))
                return

            stdout = stdout.decode('utf-8')
            stderr = stderr.decode('utf-8')

            if proc.returncode == 0:
                response = json.loads(stdout)
                self.set_header("Content-Type", "application/json")
                self.write(json.dumps(response))
            else:
                try:
                    error_data = json.loads(stdout)
                except (json.JSONDecodeError, TypeError):
                    error_data = {"errors": [{"error": stderr or "Unknown error"}]}

                self.set_status(400)
                self.set_header("Content-Type", "application/json")
                self.write(json.dumps({
                    "error_id": "PURGE_FAILED",
                    "message": "Failed to purge some entries",
                    "affected_items": error_data.get("failed", []),
                    "errors": error_data.get("errors", []),
                }))

        except (OSError, TimeoutError) as e:
            self.set_status(500)
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({
                "error_id": "INTERNAL_ERROR",
                "message": f"Failed to execute purge command: {e!s}",
                "affected_items": dns,
            }))
