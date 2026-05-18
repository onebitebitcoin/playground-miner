import json
from unittest.mock import MagicMock

import pytest
from django.test import SimpleTestCase

from blocks.api_helpers import _parse_int, _parse_float, _load_json_body


class ParseIntTests(SimpleTestCase):
    def test_integer_string(self):
        self.assertEqual(_parse_int('42'), 42)

    def test_integer_value(self):
        self.assertEqual(_parse_int(10), 10)

    def test_float_truncates(self):
        self.assertEqual(_parse_int(3.9), 3)

    def test_none_returns_default(self):
        self.assertIsNone(_parse_int(None))

    def test_none_with_custom_default(self):
        self.assertEqual(_parse_int(None, default=0), 0)

    def test_invalid_string_returns_default(self):
        self.assertIsNone(_parse_int('abc'))

    def test_empty_string_returns_default(self):
        self.assertIsNone(_parse_int(''))

    def test_negative_value(self):
        self.assertEqual(_parse_int('-5'), -5)

    def test_zero(self):
        self.assertEqual(_parse_int('0'), 0)


class ParseFloatTests(SimpleTestCase):
    def test_float_string(self):
        self.assertAlmostEqual(_parse_float('3.14'), 3.14)

    def test_integer_coerced(self):
        self.assertAlmostEqual(_parse_float(2), 2.0)

    def test_none_returns_default(self):
        self.assertIsNone(_parse_float(None))

    def test_none_with_custom_default(self):
        self.assertAlmostEqual(_parse_float(None, default=0.0), 0.0)

    def test_invalid_string_returns_default(self):
        self.assertIsNone(_parse_float('not-a-number'))

    def test_empty_string_returns_default(self):
        self.assertIsNone(_parse_float(''))

    def test_negative_float(self):
        self.assertAlmostEqual(_parse_float('-1.5'), -1.5)

    def test_scientific_notation(self):
        self.assertAlmostEqual(_parse_float('1e2'), 100.0)


class LoadJsonBodyTests(SimpleTestCase):
    def _make_request(self, body):
        req = MagicMock()
        req.body = body if isinstance(body, bytes) else body.encode('utf-8')
        return req

    def test_valid_json_bytes(self):
        req = self._make_request(b'{"key": "value"}')
        result = _load_json_body(req)
        self.assertEqual(result, {'key': 'value'})

    def test_valid_json_string_body(self):
        req = MagicMock()
        req.body = '{"x": 1}'
        result = _load_json_body(req)
        self.assertEqual(result, {'x': 1})

    def test_empty_body_returns_empty_dict(self):
        req = self._make_request(b'')
        result = _load_json_body(req)
        self.assertEqual(result, {})

    def test_whitespace_only_returns_empty_dict(self):
        req = self._make_request(b'   ')
        result = _load_json_body(req)
        self.assertEqual(result, {})

    def test_invalid_json_returns_none(self):
        req = self._make_request(b'{invalid json}')
        result = _load_json_body(req)
        self.assertIsNone(result)

    def test_array_json(self):
        req = self._make_request(b'[1, 2, 3]')
        result = _load_json_body(req)
        self.assertEqual(result, [1, 2, 3])

    def test_nested_json(self):
        payload = {'assets': [{'id': 'BTC', 'label': '비트코인'}]}
        req = self._make_request(json.dumps(payload).encode())
        result = _load_json_body(req)
        self.assertEqual(result['assets'][0]['id'], 'BTC')

    def test_body_access_raises_returns_empty_dict(self):
        req = MagicMock()
        type(req).body = property(lambda self: (_ for _ in ()).throw(Exception('no body')))
        result = _load_json_body(req)
        self.assertEqual(result, {})
