import base64
from datetime import UTC, datetime

import pytest

from app.errors import BadRequestError
from app.pagination import decode_cursor, encode_cursor


def test_cursor_round_trips():
    ts = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)
    cursor = encode_cursor(ts, 1234)

    decoded_ts, decoded_id = decode_cursor(cursor)
    assert decoded_ts == ts
    assert decoded_id == 1234


def test_decode_rejects_non_base64():
    with pytest.raises(BadRequestError):
        decode_cursor("not a cursor lol")


def test_decode_rejects_wrong_shape():
    bad_cursor = base64.urlsafe_b64encode(b"no-separator-here").decode()
    with pytest.raises(BadRequestError):
        decode_cursor(bad_cursor)
