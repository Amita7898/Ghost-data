"""Small localhost-only Ollama transport. No automatic model downloads."""

import json
import urllib.error
import urllib.request
from urllib.parse import urlsplit


class RuntimeFailure(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise RuntimeFailure("Runtime redirects are prohibited")


class Ollama:
    live = True

    def __init__(
        self, model="qwen3.5:latest", endpoint="http://127.0.0.1:11434", timeout=120
    ):
        if not 1 <= timeout <= 600:
            raise ValueError("Runtime timeout must be between 1 and 600 seconds")
        url = urlsplit(endpoint)
        if (
            url.scheme != "http"
            or url.hostname not in ("127.0.0.1", "localhost", "::1")
            or url.username
            or url.password
            or url.path not in ("", "/")
        ):
            raise ValueError("Only a local HTTP Ollama endpoint is permitted")
        if model.casefold().endswith((":cloud", "-cloud")):
            raise ValueError("Cloud models are prohibited")
        self.model = model
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        self._ready_checked = False
        self.http = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), NoRedirect()
        )

    def request(self, path, payload=None):
        req = urllib.request.Request(
            self.endpoint + path,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Content-Type": "application/json"},
        )
        try:
            with self.http.open(req, timeout=self.timeout) as response:
                raw = response.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise RuntimeFailure("Runtime response limit exceeded")
                value = json.loads(raw)
                if not isinstance(value, dict):
                    raise RuntimeFailure("Invalid runtime response")
                return value
        except (OSError, ValueError, urllib.error.URLError) as exc:
            raise RuntimeFailure(
                f"Local inference unavailable or invalid response ({type(exc).__name__}); run ghost-data doctor"
            ) from None

    def ready(self) -> dict:
        tags = self.request("/api/tags")
        models = tags.get("models", [])
        info = next((m for m in models if m.get("name") == self.model), None)
        if not info:
            raise RuntimeFailure(
                "Selected model is not installed; download only after confirming disk use"
            )
        if info.get("remote_host") or info.get("remote_model"):
            raise RuntimeFailure("Remote models are prohibited")
        show = self.request("/api/show", {"model": self.model})
        if "tools" not in show.get("capabilities", []):
            raise RuntimeFailure("Selected model does not advertise tool calling")
        self._ready_checked = True
        return {
            "runtime": self.request("/api/version"),
            "model": info,
            "capabilities": show.get("capabilities", []),
        }

    def chat(
        self,
        messages: list,
        tools: list,
        context: int = 16384,
        predict: int = 512,
        format: dict | None = None,
    ) -> dict:
        if not self._ready_checked:
            self.ready()
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": False,
            "keep_alive": "5m",
            "options": {
                "temperature": 0,
                "presence_penalty": 0,
                "seed": 42,
                "num_ctx": context,
                "num_predict": predict,
            },
        }
        if tools:
            payload["tools"] = tools
        if format:
            payload["format"] = format
        response = self.request("/api/chat", payload)
        if not response.get("done") or not isinstance(response.get("message"), dict):
            raise RuntimeFailure("Incomplete runtime response")
        return response
