"""
HTTP 客户端：封装 GET/POST，自动加 Authorization，超时与重试。
"""
import time

import requests

from .config import config

MAX_RETRIES = 3
TIMEOUT_SEC = 15


def _headers():
    return {"Authorization": f"Bearer {config.NODE_TOKEN}", "Content-Type": "application/json"}


def _request(method: str, url: str, **kwargs) -> requests.Response:
    kwargs.setdefault("headers", {}).update(_headers())
    kwargs.setdefault("timeout", TIMEOUT_SEC)
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.request(method, url, **kwargs)
            return r
        except (requests.RequestException, OSError) as e:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(1)
    raise RuntimeError("unreachable")


def get(url: str, **kwargs) -> requests.Response:
    return _request("GET", url, **kwargs)


def post(url: str, json: dict | None = None, **kwargs) -> requests.Response:
    return _request("POST", url, json=json or {}, **kwargs)
