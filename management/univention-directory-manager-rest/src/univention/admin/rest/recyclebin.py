#!/usr/bin/python3
# SPDX-FileCopyrightText: 2024-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""REST API endpoint for manual recycle bin purging."""

import json
import os
import subprocess
from typing import Dict, Any

import tornado.web
from tornado.web import HTTPError


CLEANUP_SCRIPT_PATH = '/usr/share/univention-directory-manager-tools/univention-recycle-bin-clean-expired-entries'


class RecycleBinPurge(tornado.web.RequestHandler):
    """Manually purge specific recycle bin entries."""

    async def post(self):
        """Handle POST request to purge recycle bin entries.
        
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
            "--json-output"
        ]
        
        try:
            env = os.environ.copy()
            env['MANUAL_ACTOR_DN'] = user_dn
            
            result = subprocess.run(
                cmd,
                input=dns_input,
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            if result.returncode == 0:
                response = json.loads(result.stdout)
                self.set_header("Content-Type", "application/json")
                self.write(json.dumps(response))
            else:
                try:
                    error_data = json.loads(result.stdout)
                except:
                    error_data = {"errors": [{"error": result.stderr or "Unknown error"}]}
                
                self.set_status(400)
                self.set_header("Content-Type", "application/json")
                self.write(json.dumps({
                    "error_id": "PURGE_FAILED",
                    "message": "Failed to purge some entries",
                    "affected_items": error_data.get("failed", []),
                    "errors": error_data.get("errors", [])
                }))
        
        except subprocess.TimeoutExpired:
            self.set_status(504)
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({
                "error_id": "TIMEOUT",
                "message": "Purge operation timed out after 30 seconds",
                "affected_items": dns
            }))
        except subprocess.SubprocessError as e:
            self.set_status(500)
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({
                "error_id": "INTERNAL_ERROR",
                "message": f"Failed to execute purge command: {str(e)}",
                "affected_items": dns
            }))