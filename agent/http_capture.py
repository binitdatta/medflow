"""
Wire-level capture of the actual HTTP request/response the Anthropic SDK
sends -- not the LangChain-level message list (agent/graph.py's llm_call_log
write already captures that reliably on its own), the real HTTP method, URL,
headers, and body as they left this process.

WHY A MONKEYPATCH: the Anthropic Python SDK is built on httpx. Rather than
depend on langchain-anthropic's ChatAnthropic accepting a custom
`http_client` constructor kwarg -- which may or may not be supported
depending on the exact installed version, and would silently stop working
on an upgrade -- this patches httpx.Client.send (and AsyncClient.send)
directly. That's the one place every outbound call passes through
regardless of how the client object above it was constructed. This is the
same technique APM/observability tools (Datadog, New Relic, etc.) use for
exactly this kind of cross-cutting instrumentation.

This only affects httpx traffic. MedFlow's own internal REST calls
(agent/api_client.py) and Keycloak calls (auth/keycloak.py) both use the
`requests` library, not httpx, so they're untouched by this.

SECURITY: the API key header is redacted before anything is captured --
never stored, never logged, never visible to a HIPAA reviewer.
"""
import contextvars
import httpx

_capture_ctx: contextvars.ContextVar = contextvars.ContextVar("llm_http_capture", default=None)
_REDACTED_HEADERS = {"x-api-key", "authorization"}
_patched = False


def _redact_headers(headers) -> dict:
    return {k: ("***REDACTED***" if k.lower() in _REDACTED_HEADERS else v) for k, v in headers.items()}


def _record_request(request: httpx.Request):
    ctx = _capture_ctx.get()
    if ctx is None or "anthropic.com" not in str(request.url):
        return
    ctx["http_method"] = request.method
    ctx["url"] = str(request.url)
    ctx["request_headers"] = _redact_headers(request.headers)
    try:
        ctx["request_body"] = request.content.decode("utf-8")
    except Exception:
        ctx["request_body"] = None


def _record_response(response: httpx.Response):
    ctx = _capture_ctx.get()
    if ctx is None:
        return
    try:
        response.read()
        ctx["response_status"] = response.status_code
        ctx["response_body"] = response.text
    except Exception:
        ctx["response_status"] = getattr(response, "status_code", None)
        ctx["response_body"] = None


def install_http_capture():
    """Call once at app startup (see app.py). Idempotent -- safe to call
    more than once (e.g. under the debug reloader)."""
    global _patched
    if _patched:
        return
    _patched = True

    _orig_send = httpx.Client.send

    def _patched_send(self, request, *args, **kwargs):
        _record_request(request)
        response = _orig_send(self, request, *args, **kwargs)
        _record_response(response)
        return response

    httpx.Client.send = _patched_send

    if hasattr(httpx, "AsyncClient"):
        _orig_asend = httpx.AsyncClient.send

        async def _patched_asend(self, request, *args, **kwargs):
            _record_request(request)
            response = await _orig_asend(self, request, *args, **kwargs)
            _record_response(response)
            return response

        httpx.AsyncClient.send = _patched_asend


class capture_llm_http_call:
    """Context manager: everything captured during the `with` block lands in
    the returned dict. Safe under Flask's synchronous request handling --
    each request's LLM call happens within one call stack on one thread, so
    the contextvar value never leaks across concurrent requests.

    Usage:
        with capture_llm_http_call() as http_capture:
            response = llm.invoke(messages)
        # http_capture now has: http_method, url, request_headers,
        # request_body, response_status, response_body (any may be absent
        # if the underlying call never reached httpx, e.g. it errored
        # before making a request).
    """
    def __enter__(self):
        self._data = {}
        self._token = _capture_ctx.set(self._data)
        return self._data

    def __exit__(self, exc_type, exc_val, exc_tb):
        _capture_ctx.reset(self._token)
        return False