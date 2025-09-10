#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""REST API endpoint for manual recycle bin purging."""

import asyncio
import json
import os

from tornado.web import HTTPError

from univention.admin.rest.module import Resource
from univention.lib.i18n import Translation


_ = Translation('univention-directory-manager-rest').translate


# Constants
PURGE_TIMEOUT_SECONDS = 30
CLEANUP_SCRIPT_PATH = '/usr/share/univention-directory-manager-tools/univention-recycle-bin-clean-expired-entries'


class RecycleBinPurge(Resource):
    """Manually purge specific recycle bin entries."""

    async def post(self):
        """
        Handle POST request to purge recycle bin entries.

        Expects JSON body with 'dns' field containing list of DNs to purge.
        Returns structured JSON response with success/error details.

        :raises HTTPError: For invalid requests or processing errors
        """
        if not hasattr(self.request, 'user_dn') or not self.request.user_dn:
            raise HTTPError(401, _("Authentication required"))

        if not self._check_purge_permission():
            raise HTTPError(403, _("Insufficient privileges to purge recycle bin entries"))

        try:
            body = json.loads(self.request.body)
        except (json.JSONDecodeError, TypeError):
            raise HTTPError(400, _("Invalid JSON in request body"))

        dns = body.get('dns', [])
        if not dns:
            raise HTTPError(400, _("'dns' list cannot be empty"))

        if not isinstance(dns, list):
            raise HTTPError(400, _("'dns' must be a list"))

        # Validate all DNs
        for dn in dns:
            if not isinstance(dn, str):
                raise HTTPError(400, _("All DNs must be strings"))
            if not self._is_valid_dn_format(dn):
                raise HTTPError(400, _("Invalid DN format: %s") % dn)
            if self._contains_shell_metacharacters(dn):
                raise HTTPError(400, _("Invalid DN format: %s") % dn)
            # Verify DN is in recyclebin container
            if not self._verify_recyclebin_dn(dn):
                raise HTTPError(400, _("DN is not in recycle bin: %s") % dn)

        # Execute purge operation
        result = await self._execute_purge(dns)

        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(result))

    async def _execute_purge(self, dns):
        """
        Execute the purge operation via the cleanup script.

        :param dns: List of DNs to purge
        :type dns: list
        :return: Result dictionary with purge status
        :rtype: dict
        """
        try:
            # Set environment variable for actor tracking
            env = os.environ.copy()
            env['MANUAL_ACTOR_DN'] = self.request.user_dn or 'unknown'

            # Prepare DNs for stdin
            dns_input = '\n'.join(dns).encode('utf-8')

            # Execute the cleanup script
            process = await asyncio.create_subprocess_exec(
                CLEANUP_SCRIPT_PATH,
                '--purge-dns-stdin',
                '--remove-expired',
                '--json-output',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=dns_input),
                    timeout=PURGE_TIMEOUT_SECONDS,
                )
            except TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "error": {
                        "id": "PURGE_TIMEOUT",
                        "message": "Purge operation timed out after %d seconds" % PURGE_TIMEOUT_SECONDS,
                        "affected_items": dns,
                    },
                }

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace') if stderr else "Unknown error"
                return {
                    "success": False,
                    "error": {
                        "id": "PURGE_FAILED",
                        "message": "Purge operation failed: %s" % error_msg,
                        "affected_items": dns,
                    },
                }

            # Parse JSON output from script
            try:
                result = json.loads(stdout.decode('utf-8'))
                # Ensure structured error format if there are failures
                if not result.get("success") and result.get("failed"):
                    result["error"] = {
                        "id": "PARTIAL_FAILURE",
                        "message": "Some items could not be purged",
                        "affected_items": result.get("failed", []),
                    }
                return result
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": {
                        "id": "INVALID_RESPONSE",
                        "message": "Invalid response from purge script",
                        "affected_items": dns,
                    },
                }

        except Exception as e:
            return {
                "success": False,
                "error": {
                    "id": "INTERNAL_ERROR",
                    "message": "Failed to execute purge command: %s" % e,
                    "affected_items": dns,
                },
            }

    def _check_purge_permission(self):
        """
        Check if the current user has permission to purge recycle bin entries.

        :return: True if user has permission, False otherwise
        :rtype: bool
        """
        # Check if user is Domain Admin
        if hasattr(self, 'lo') and self.lo:
            try:
                user_dn = self.request.user_dn
                if not user_dn:
                    return False

                # Check if user is in Domain Admins group
                domain_admins_dn = "cn=Domain Admins,cn=groups,%s" % self.lo.base
                result = self.lo.search(
                    base=domain_admins_dn,
                    scope='base',
                    filter='(uniqueMember=%s)' % user_dn,
                    attr=['cn'],
                )
                if result:
                    return True
            except Exception:
                pass

        return False

    def _verify_recyclebin_dn(self, dn):
        """
        Verify that the DN is in the recycle bin container.

        :param dn: Distinguished name to verify
        :type dn: str
        :return: True if DN is in recycle bin, False otherwise
        :rtype: bool
        """
        return 'cn=recyclebin,cn=internal' in dn.lower()

    def _is_valid_dn_format(self, dn):
        """
        Basic DN format validation.

        :param dn: Distinguished name to validate
        :type dn: str
        :return: True if DN format appears valid
        :rtype: bool
        """
        return '=' in dn and ',' in dn

    def _contains_shell_metacharacters(self, dn):
        """
        Check for shell metacharacters that could be dangerous.

        :param dn: Distinguished name to check
        :type dn: str
        :return: True if dangerous characters found
        :rtype: bool
        """
        dangerous_chars = ['$', '`', '\\', '"', "'", ';', '&', '|', '>', '<', '(', ')', '{', '}', '[', ']', '*', '?', '~', '!']
        return any(char in dn for char in dangerous_chars)
