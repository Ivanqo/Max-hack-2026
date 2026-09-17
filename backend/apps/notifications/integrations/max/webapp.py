from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl

from django.conf import settings


class MaxInitDataError(ValueError):
    """Raised when MAX mini-app initData cannot be trusted."""


@dataclass(frozen=True)
class MaxLaunchContext:
    max_user_id: str
    username: str = ''
    first_name: str = ''
    last_name: str = ''
    start_param: str = ''
    auth_date: int | None = None
    raw: dict[str, Any] | None = None


def validate_init_data(init_data: str, allow_mock: bool | None = None) -> MaxLaunchContext:
    """
    Validate MAX WebAppData/initData and return the linked MAX user.

    MAX mini apps use signed launch data. The check mirrors the official
    WebAppData flow: sort fields except hash, build a newline-delimited data
    check string, derive the HMAC key from "WebAppData" and the bot token,
    then compare the hex digest in constant time.
    """
    allow_mock = (
        getattr(settings, 'MAX_INTEGRATION_MODE', 'mock') != 'real'
        if allow_mock is None else allow_mock
    )
    params = _parse_init_data(init_data)
    if not params:
        raise MaxInitDataError('MAX initData is empty')

    supplied_hash = params.get('hash')
    if supplied_hash:
        _verify_hash(params, supplied_hash)
        _verify_auth_date(params)
    elif not allow_mock:
        raise MaxInitDataError('MAX initData signature is missing')

    user = _extract_user(params)
    max_user_id = str(
        user.get('id')
        or user.get('user_id')
        or params.get('max_user_id')
        or params.get('user_id')
        or ''
    ).strip()
    if not max_user_id:
        raise MaxInitDataError('MAX user id is missing')

    return MaxLaunchContext(
        max_user_id=max_user_id,
        username=str(user.get('username') or user.get('login') or params.get('username') or ''),
        first_name=str(user.get('first_name') or user.get('firstName') or ''),
        last_name=str(user.get('last_name') or user.get('lastName') or ''),
        start_param=str(params.get('start_param') or params.get('startPayload') or params.get('payload') or ''),
        auth_date=_safe_int(params.get('auth_date')),
        raw=params,
    )


def _parse_init_data(init_data: str) -> dict[str, str]:
    if not init_data:
        return {}
    init_data = init_data.strip().lstrip('#')
    if init_data.startswith('mock:'):
        return {
            'max_user_id': init_data.removeprefix('mock:'),
            'username': 'mock_student',
        }
    pairs = parse_qsl(init_data, keep_blank_values=True)
    outer = dict(pairs)
    for key in ['WebAppData', 'web_app_data', 'initData', 'init_data']:
        nested = outer.get(key)
        if nested and nested != init_data:
            return _parse_init_data(nested)

    params: dict[str, str] = {}
    for key, value in pairs:
        if key in params:
            raise MaxInitDataError('MAX initData contains duplicate fields')
        params[key] = value
    return params


def _verify_hash(params: dict[str, str], supplied_hash: str) -> None:
    token = getattr(settings, 'MAX_BOT_TOKEN', '')
    if not token:
        raise MaxInitDataError('MAX bot token is not configured')
    data_check_string = '\n'.join(
        f'{key}={value}'
        for key, value in sorted(params.items())
        if key != 'hash'
    )
    secret_key = hmac.new(b'WebAppData', token.encode(), hashlib.sha256).digest()
    calculated = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(calculated, supplied_hash):
        raise MaxInitDataError('MAX initData signature is invalid')


def _verify_auth_date(params: dict[str, str]) -> None:
    auth_date = _safe_int(params.get('auth_date'))
    if not auth_date:
        return
    max_age = getattr(settings, 'MAX_INITDATA_MAX_AGE_SECONDS', 86400)
    if max_age > 0 and time.time() - auth_date > max_age:
        raise MaxInitDataError('MAX initData is expired')


def _extract_user(params: dict[str, str]) -> dict[str, Any]:
    for key in ['user', 'web_app_user', 'sender']:
        raw = params.get(key)
        if not raw:
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MaxInitDataError('MAX user payload is malformed') from exc
        if isinstance(value, dict):
            return value
    return {}


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
