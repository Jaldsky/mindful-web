"""Типы и алиасы для HTTP-запросов."""

from collections.abc import Awaitable, Callable
from typing import Any

import httpx

Headers = dict[str, str]
Params = dict[str, Any]
Cookies = Any
RequestData = Any
RequestJson = Any
RequestFiles = Any
RequestContent = Any

RequestOperation = Callable[[], Awaitable[httpx.Response]]
