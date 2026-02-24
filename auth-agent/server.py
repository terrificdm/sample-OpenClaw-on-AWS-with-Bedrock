"""
Authorization Agent HTTP server.

Receives PermissionRequest payloads from Agent Containers via AgentCore Runtime
/invocations endpoint, processes them through handler.py, and returns the result.

This is the entry point for the Authorization Agent Docker container.
"""
import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# Ensure auth-agent modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from permission_request import PermissionRequest
from handler import handle_permission_request, handle_pending_approvals_command


class AuthAgentHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A002
        logger.info(format, *args)

    def do_GET(self):
        if self.path == "/ping":
            self._respond(200, {"status": "ok", "role": "auth-agent"})
        else:
            self._respond(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/invocations":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)

            try:
                payload = json.loads(body)
            except json.JSONDecodeError as e:
                logger.error("Failed to parse request body: %s", e)
                self._respond(400, {"error": "invalid json"})
                return

            # Handle /pending approvals command
            message = payload.get("message", "")
            if message.strip().lower() in ("/pending approvals", "pending approvals"):
                result = handle_pending_approvals_command()
                self._respond(200, {"response": result})
                return

            # Handle PermissionRequest payload
            try:
                request = PermissionRequest(
                    request_id=payload["request_id"],
                    tenant_id=payload["tenant_id"],
                    resource_type=payload["resource_type"],
                    resource=payload["resource"],
                    reason=payload.get("reason", ""),
                    duration_type=payload.get("duration_type", "temporary"),
                    suggested_duration_hours=payload.get("suggested_duration_hours", 1),
                    requested_at=datetime.fromisoformat(payload["requested_at"]),
                    expires_at=datetime.fromisoformat(payload["expires_at"]),
                    status=payload.get("status", "pending"),
                )
                result = handle_permission_request(request)
                self._respond(200, result)
            except (KeyError, ValueError) as e:
                logger.error("Invalid PermissionRequest payload: %s", e)
                self._respond(400, {"error": f"invalid payload: {e}"})
        else:
            self._respond(404, {"error": "not found"})

    def _respond(self, status: int, body: dict):
        data = json.dumps(body, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), AuthAgentHandler)
    logger.info(
        "Authorization Agent listening on port %d (session_id=auth-agent-%s)",
        port,
        os.environ.get("STACK_NAME", "dev"),
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
