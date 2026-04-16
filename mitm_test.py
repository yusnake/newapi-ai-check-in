"""
MITM proxy test: starts a simple HTTP proxy on port 8080 that logs all
request headers and URLs to mitm_log.txt, then uses the Anthropic SDK
with ANTHROPIC_BASE_URL pointing to the proxy.
"""

import os
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

import httpx
import anthropic

LOG_FILE = os.path.join(os.path.dirname(__file__), 'mitm_log.txt')
PROXY_PORT = 8080
# Use the pre-existing ANTHROPIC_BASE_URL as the upstream if set, otherwise
# fall back to the official Anthropic API.
_env_base = os.environ.get('ANTHROPIC_BASE_URL', 'https://api.anthropic.com')
ANTHROPIC_UPSTREAM = _env_base.rstrip('/')

# ── proxy implementation ──────────────────────────────────────────────────────

def _log(message: str) -> None:
    with open(LOG_FILE, 'a') as f:
        f.write(message + '\n')
    print(message)


class MITMHandler(BaseHTTPRequestHandler):
    """Minimal logging HTTP proxy."""

    # silence default request-line log so our structured log is the only output
    def log_message(self, fmt, *args):  # noqa: N802
        pass

    def _forward(self, body: bytes | None = None) -> None:
        # Reconstruct the upstream URL.
        # The SDK sends requests to http://localhost:8080/anthropic/<path>
        # We strip the /anthropic prefix and forward to api.anthropic.com.
        path = self.path  # e.g. /anthropic/v1/messages
        if path.startswith('/anthropic'):
            upstream_path = path[len('/anthropic'):]  # e.g. /v1/messages
        else:
            upstream_path = path

        upstream_url = ANTHROPIC_UPSTREAM + upstream_path

        # Collect headers, drop hop-by-hop ones
        headers = {}
        hop_by_hop = {
            'connection', 'keep-alive', 'proxy-authenticate',
            'proxy-authorization', 'te', 'trailers', 'transfer-encoding',
            'upgrade', 'host',
            # Strip encoding negotiation so upstream returns raw bytes we can
            # forward verbatim without double-decompression on the SDK side.
            'accept-encoding',
        }
        for key, value in self.headers.items():
            if key.lower() not in hop_by_hop:
                headers[key] = value

        # ── log the intercepted request ───────────────────────────────────────
        separator = '=' * 72
        entry = [
            '',
            separator,
            f'TIMESTAMP : {datetime.utcnow().isoformat()}Z',
            f'METHOD    : {self.command}',
            f'URL       : {upstream_url}',
            'HEADERS   :',
        ]
        for k, v in headers.items():
            # Redact the key value in the log for safety
            display_v = v[:12] + '...' if k.lower() == 'x-api-key' else v
            entry.append(f'  {k}: {display_v}')
        if body:
            entry.append(f'BODY      : {body.decode(errors="replace")[:500]}')
        entry.append(separator)
        _log('\n'.join(entry))
        # ─────────────────────────────────────────────────────────────────────

        # Forward to upstream
        with httpx.Client(timeout=60) as client:
            resp = client.request(
                method=self.command,
                url=upstream_url,
                headers=headers,
                content=body,
            )

        # Return upstream response to the SDK.
        # httpx auto-decompresses the body, so we must strip Content-Encoding
        # to avoid double-decompression on the SDK side.
        skip_resp_headers = {'transfer-encoding', 'connection', 'content-encoding'}
        self.send_response(resp.status_code)
        for k, v in resp.headers.items():
            if k.lower() not in skip_resp_headers:
                self.send_header(k, v)
        # Update Content-Length to reflect the decompressed body length
        self.send_header('Content-Length', str(len(resp.content)))
        self.end_headers()
        self.wfile.write(resp.content)

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length) if length else None
        self._forward(body)

    def do_GET(self):  # noqa: N802
        self._forward()


def start_proxy() -> HTTPServer:
    server = HTTPServer(('127.0.0.1', PROXY_PORT), MITMHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    # Clear previous log
    open(LOG_FILE, 'w').close()

    print(f'[mitm_test] Starting proxy on port {PROXY_PORT} …')
    server = start_proxy()
    time.sleep(0.3)  # give the server a moment to bind

    # Point the SDK at our proxy
    base_url = f'http://127.0.0.1:{PROXY_PORT}/anthropic'
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')

    _log(f'[mitm_test] Proxy ready. Forwarding: {base_url} → {ANTHROPIC_UPSTREAM}')
    _log(f'[mitm_test] SDK base_url = {base_url}')

    print(f'[mitm_test] Sending test message via Anthropic SDK (base_url={base_url}) …')

    client = anthropic.Anthropic(api_key=api_key, base_url=base_url)

    message = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=64,
        messages=[{'role': 'user', 'content': 'Say "MITM proxy test successful" and nothing else.'}],
    )

    reply = message.content[0].text if message.content else '(empty)'
    print(f'[mitm_test] Model reply: {reply}')
    _log(f'\n[mitm_test] Model reply: {reply}')
    _log('[mitm_test] Test complete.')

    server.shutdown()
    print(f'[mitm_test] Done. Log written to {LOG_FILE}')


if __name__ == '__main__':
    main()
