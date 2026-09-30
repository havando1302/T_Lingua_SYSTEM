"""Opt-in, bounded local HTTP baseline. Never run automatically by capture/tests."""
from __future__ import annotations

import ipaddress
import http.client
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request

from .common import Phase1Error, utc_now


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _validate_url(base_url: str) -> str:
    parsed = urllib.parse.urlsplit(base_url)
    try:
        loopback = parsed.hostname == "localhost" or ipaddress.ip_address(parsed.hostname or "").is_loopback
        port = parsed.port
    except ValueError:
        raise Phase1Error("Benchmark requires a valid loopback HTTP(S) base URL.") from None
    if (not loopback or parsed.scheme not in {"http", "https"} or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path not in {"", "/"}):
        raise Phase1Error("Benchmark only supports loopback URLs without credentials, query or path.")
    # Replace localhost with a literal address so proxy/DNS settings cannot redirect the workload.
    host = "127.0.0.1" if parsed.hostname == "localhost" else parsed.hostname
    if ":" in host:
        host = "[" + host + "]"
    return f"{parsed.scheme}://{host}" + (f":{port}" if port else "")


def benchmark_http(base_url: str, *, samples: int = 3, timeout_seconds: float = 30) -> dict:
    if not 1 <= samples <= 10 or not 0 < timeout_seconds <= 60:
        raise Phase1Error("Use 1-10 samples and a timeout greater than 0 and at most 60 seconds.")
    url = _validate_url(base_url) + "/api/translate-text"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    # No real user input and no endpoints that create history/TM/QA records.
    payload = json.dumps({"text": "Hello, this is a synthetic baseline sample.",
                          "source_lang": "en", "target_lang": "vi"}).encode("utf-8")
    measurements = []
    for index in range(samples):
        started = time.perf_counter()
        request = urllib.request.Request(url, data=payload, method="POST",
                                         headers={"Content-Type": "application/json"})
        try:
            with opener.open(request, timeout=timeout_seconds) as response:
                content = response.read(1024 * 1024 + 1)
                if len(content) > 1024 * 1024:
                    raise ValueError("Response exceeded measurement limit.")
                decoded = json.loads(content)
                if not isinstance(decoded, dict) or not isinstance(decoded.get("translated_text"), str):
                    raise ValueError("Response contract mismatch.")
                if not decoded["translated_text"].strip():
                    raise ValueError("Empty translated text.")
            measurements.append({"sample": index + 1, "status": "success",
                                 "elapsed_ms": round((time.perf_counter() - started) * 1000, 3)})
        except (OSError, ValueError, urllib.error.URLError, http.client.HTTPException) as error:
            measurements.append({"sample": index + 1, "status": "failed",
                                 "error_type": type(error).__name__,
                                 "elapsed_ms": round((time.perf_counter() - started) * 1000, 3)})
            break  # A failed service is not subjected to repeated workload.
    durations = sorted(row["elapsed_ms"] for row in measurements if row["status"] == "success")
    complete = len(durations) == samples
    return {"format_version": 1, "created_at": utc_now(),
            "status": "measured" if complete else "incomplete", "requested_samples": samples,
            "scope": "sequential_local_text_http_client_latency_including_server_work",
            "workload": "one_repeated_synthetic_en_to_vi_text_no_warmup",
            "samples": measurements,
            "statistics": {"successful_samples": len(durations),
                           "p50_ms": durations[math.ceil(len(durations) * .5) - 1] if durations else None,
                           "p95_ms": durations[math.ceil(len(durations) * .95) - 1] if durations else None},
            "limitations": ["small sample descriptive baseline, not capacity/SLO evidence",
                            "timeout bounds socket operations, not a strict overall request deadline",
                            "TM/model hit path and warm/cold state not independently observed",
                            "no STT, TTS, GPU resource, queue or microphone end-to-end measurement",
                            "backend's existing application logging behavior still applies"],
            "response_content_stored": False}
