"""
Agent Container HTTP server.

Wraps openclaw as a subprocess. For each /invocations request:
  A. Injects the tenant's allowed tools into the system prompt (soft enforcement).
  E. Audits the response for tool usage patterns (post-execution logging).
"""
import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from permissions import read_permission_profile
from observability import log_agent_invocation, log_permission_denied
from safety import validate_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OPENCLAW_PORT = 18789
OPENCLAW_URL = f"http://localhost:{OPENCLAW_PORT}"
STARTUP_TIMEOUT = 30

# Regex to detect tool invocation patterns in openclaw responses.
# openclaw typically outputs tool calls as: [tool_name] or <tool:tool_name> or similar.
_TOOL_PATTERN = re.compile(
    r'\b(shell|browser|file_write|code_execution|install_skill|load_extension|eval)\b',
    re.IGNORECASE,
)


def _build_system_prompt(tenant_id: str) -> str:
    """Plan A: build a system prompt that constrains openclaw to allowed tools."""
    try:
        profile = read_permission_profile(tenant_id)
        allowed = profile.get("tools", ["web_search"])
        blocked = [t for t in ["shell", "browser", "file", "file_write", "code_execution",
                                "install_skill", "load_extension", "eval"]
                   if t not in allowed]
    except Exception:
        allowed = ["web_search"]
        blocked = ["shell", "browser", "file", "file_write", "code_execution",
                   "install_skill", "load_extension", "eval"]

    lines = [
        f"Allowed tools for this session: {', '.join(allowed)}.",
    ]
    if blocked:
        lines.append(
            f"You MUST NOT use these tools: {', '.join(blocked)}. "
            "If the user requests an action that requires a blocked tool, "
            "explain that you don't have permission and they should contact their administrator."
        )
    return " ".join(lines)


def _audit_response(tenant_id: str, response_text: str, allowed_tools: list) -> None:
    """Plan E: scan response for tool usage and log any violations."""
    matches = _TOOL_PATTERN.findall(response_text)
    if not matches:
        return
    for tool in set(t.lower() for t in matches):
        if tool not in allowed_tools:
            log_permission_denied(
                tenant_id=tenant_id,
                tool_name=tool,
                cedar_decision="RESPONSE_AUDIT",
                request_id=None,
            )
            logger.warning(
                "AUDIT: blocked tool '%s' detected in response tenant_id=%s",
                tool, tenant_id,
            )


def start_openclaw() -> subprocess.Popen:
    config_src = "/app/openclaw.json"
    config_dst = "/tmp/openclaw_runtime.json"
    with open(config_src) as f:
        config_str = f.read()
    config_str = config_str.replace("${AWS_REGION}", os.environ.get("AWS_REGION", "us-east-1"))
    config_str = config_str.replace(
        "${BEDROCK_MODEL_ID}",
        os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0"),
    )
    with open(config_dst, "w") as f:
        f.write(config_str)

    env = os.environ.copy()
    env["OPENCLAW_SKIP_ONBOARDING"] = "1"
    proc = subprocess.Popen(
        ["openclaw", "--config", config_dst],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    threading.Thread(
        target=lambda: [logger.info("[openclaw] %s", l.decode().rstrip()) for l in proc.stdout],
        daemon=True,
    ).start()
    return proc


def wait_for_openclaw(timeout: int = STARTUP_TIMEOUT) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.post(
                f"{OPENCLAW_URL}/v1/chat/completions",
                json={"model": "probe", "messages": [], "user": "healthcheck"},
                timeout=2,
            )
            if r.status_code < 500:
                logger.info("openclaw ready (status=%d)", r.status_code)
                return
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    logger.error("openclaw did not become ready within %d seconds", timeout)
    sys.exit(1)


class AgentCoreHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A002
        logger.info(format, *args)

    def do_GET(self):
        if self.path == "/ping":
            self._respond(200, {"status": "ok"})
        else:
            self._respond(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/invocations":
            self._respond(404, {"error": "not found"})
            return

        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, {"error": "invalid json"})
            return

        tenant_id = payload.get("sessionId") or payload.get("tenant_id") or "unknown"
        message = validate_message(payload.get("message", ""))
        session_key = f"agentcore:{tenant_id}"

        # Plan A: inject permission constraints into system prompt
        system_prompt = _build_system_prompt(tenant_id)

        start_ms = int(time.time() * 1000)
        try:
            resp = requests.post(
                f"{OPENCLAW_URL}/v1/chat/completions",
                json={
                    "model": payload.get("model", "default"),
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message},
                    ],
                    "user": session_key,
                },
                timeout=300,
            )
            result = resp.json()
            duration_ms = int(time.time() * 1000) - start_ms

            # Plan E: audit the response for tool usage
            response_text = json.dumps(result)
            try:
                profile = read_permission_profile(tenant_id)
                allowed = profile.get("tools", ["web_search"])
            except Exception:
                allowed = ["web_search"]
            _audit_response(tenant_id, response_text, allowed)

            log_agent_invocation(tenant_id=tenant_id, tools_used=[], duration_ms=duration_ms, status="success")
            self._respond(200, result)

        except Exception as e:
            duration_ms = int(time.time() * 1000) - start_ms
            log_agent_invocation(tenant_id=tenant_id, tools_used=[], duration_ms=duration_ms, status="error")
            logger.error("openclaw invocation failed tenant_id=%s error=%s", tenant_id, e)
            self._respond(500, {"error": str(e)})

    def _respond(self, status: int, body: dict):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    proc = start_openclaw()
    wait_for_openclaw(STARTUP_TIMEOUT)
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), AgentCoreHandler)
    logger.info("Python wrapper listening on port %d", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        proc.terminate()


if __name__ == "__main__":
    main()
