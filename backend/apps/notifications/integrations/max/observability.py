import json
import logging
import uuid


_SAFE_FIELDS = {
    'correlation_id',
    'event',
    'mode',
    'provider',
    'result',
    'role',
    'stage',
    'update_type',
}


def new_correlation_id() -> str:
    return uuid.uuid4().hex


def log_max_event(logger: logging.Logger, event: str, correlation_id: str, **fields) -> None:
    """Emit a small JSON record while rejecting identity and credential fields."""
    record = {
        'event': event,
        'correlation_id': correlation_id,
    }
    for key, value in fields.items():
        if key not in _SAFE_FIELDS or key in record:
            continue
        if isinstance(value, (str, int, bool)) and len(str(value)) <= 100:
            record[key] = value
    logger.info(json.dumps(record, ensure_ascii=False, separators=(',', ':'), sort_keys=True))
