from datetime import datetime

from django.test import SimpleTestCase

from blocks import views
from blocks.views import (
    _sanitize_custom_assets,
    _build_requested_assets,
    _asset_entry_is_bitcoin,
    _infer_capital_gains_tax_rate,
    _safe_float,
    _build_asset_series,
)


class SafeFloatTests(SimpleTestCase):
    def test_valid_positive(self):
        self.assertAlmostEqual(_safe_float(3.5), 3.5)

    def test_valid_string(self):
        self.assertAlmostEqual(_safe_float('2.7'), 2.7)

    def test_none_returns_none(self):
        self.assertIsNone(_safe_float(None))

    def test_negative_blocked_by_default(self):
        self.assertIsNone(_safe_float(-1.0, allow_negative=False))

    def test_negative_allowed(self):
        self.assertAlmostEqual(_safe_float(-1.0, allow_negative=True), -1.0)

    def test_zero_allowed(self):
        self.assertAlmostEqual(_safe_float(0.0, allow_negative=False), 0.0)

    def test_invalid_string_returns_none(self):
        self.assertIsNone(_safe_float('not-a-number'))


class InferCapitalGainsTaxRateTests(SimpleTestCase):
    def _cfg(self, unit='USD', category='미국 주식'):
        return {'unit': unit, 'category': category, 'ticker': ''}

    def test_us_stock_22_percent(self):
        rate = _infer_capital_gains_tax_rate(self._cfg(unit='USD', category='미국 주식'))
        self.assertAlmostEqual(rate, 0.22)

    def test_us_etf_22_percent(self):
        rate = _infer_capital_gains_tax_rate(self._cfg(unit='USD', category='미국 ETF'))
        self.assertAlmostEqual(rate, 0.22)

    def test_krw_asset_zero(self):
        rate = _infer_capital_gains_tax_rate(self._cfg(unit='KRW', category='국내 주식'))
        self.assertEqual(rate, 0.0)

    def test_unknown_asset_zero(self):
        rate = _infer_capital_gains_tax_rate(self._cfg(unit='???', category='기타'))
        self.assertEqual(rate, 0.0)


class AssetIsBitcoinTests(SimpleTestCase):
    def test_bitcoin_id(self):
        self.assertTrue(_asset_entry_is_bitcoin({'id': 'bitcoin', 'ticker': 'BTC-USD'}))

    def test_btc_usd_ticker(self):
        self.assertTrue(_asset_entry_is_bitcoin({'id': 'btc', 'ticker': 'BTC-USD'}))

    def test_non_bitcoin(self):
        self.assertFalse(_asset_entry_is_bitcoin({'id': 'AAPL', 'ticker': 'AAPL'}))

    def test_empty(self):
        self.assertFalse(_asset_entry_is_bitcoin({}))


class SanitizeCustomAssetsTests(SimpleTestCase):
    def test_strips_whitespace(self):
        result = _sanitize_custom_assets(['  AAPL  ', '삼성전자'])
        self.assertEqual(result[0]['id'], 'AAPL')
        self.assertEqual(result[1]['label'], '삼성전자')

    def test_dict_entry_preserved(self):
        entry = {'id': 'SPY', 'label': 'S&P500', 'ticker': 'SPY', 'category': '미국 ETF'}
        result = _sanitize_custom_assets([entry])
        self.assertEqual(result[0]['id'], 'SPY')
        self.assertEqual(result[0]['category'], '미국 ETF')

    def test_synthetic_asset_preserved(self):
        entry = {
            'id': 'SYNTH-DEPOSIT-0350',
            'label': '예금 3.5%',
            'ticker': 'SYNTH-DEPOSIT-0350',
            'synthetic_asset': 'deposit',
            'target_rate_pct': 3.5,
            'category': '예적금',
        }
        result = _sanitize_custom_assets([entry])
        self.assertEqual(result[0]['synthetic_asset'], 'deposit')
        self.assertAlmostEqual(result[0]['target_rate_pct'], 3.5)

    def test_empty_input(self):
        self.assertEqual(_sanitize_custom_assets([]), [])

    def test_none_input(self):
        self.assertEqual(_sanitize_custom_assets(None), [])


class BuildRequestedAssetsTests(SimpleTestCase):
    def test_bitcoin_injected_when_missing(self):
        entries = [{'id': 'AAPL', 'label': '애플', 'ticker': 'AAPL'}]
        assets = _build_requested_assets(entries, 'cagr')
        labels = [a['label'] for a in assets]
        self.assertIn('비트코인', labels)

    def test_bitcoin_first(self):
        entries = [{'id': 'AAPL', 'label': '애플', 'ticker': 'AAPL'}]
        assets = _build_requested_assets(entries, 'cagr')
        self.assertTrue(_asset_entry_is_bitcoin(assets[0]))

    def test_deduplication(self):
        entries = [
            {'id': 'bitcoin', 'label': '비트코인', 'ticker': 'BTC-USD'},
            {'id': 'bitcoin', 'label': '비트코인', 'ticker': 'BTC-USD'},
        ]
        assets = _build_requested_assets(entries, 'cagr')
        btc = [a for a in assets if _asset_entry_is_bitcoin(a)]
        self.assertEqual(len(btc), 1)

    def test_empty_list_still_has_bitcoin(self):
        assets = _build_requested_assets([], 'cagr')
        self.assertTrue(any(_asset_entry_is_bitcoin(a) for a in assets))


class BuildAssetSeriesTests(SimpleTestCase):
    def _history(self):
        return [
            (datetime(2020, 12, 31), 100.0),
            (datetime(2021, 12, 31), 121.0),
            (datetime(2022, 12, 31), 144.0),
        ]

    def _cfg(self):
        return {'id': 'TEST', 'label': '테스트', 'ticker': 'TST', 'unit': 'USD', 'category': '미국 주식'}

    def test_cagr_multiple(self):
        series = _build_asset_series('TEST', self._cfg(), self._history(), 2020, 2022, 'cagr')
        self.assertIsNotNone(series)
        self.assertAlmostEqual(series['multiple_from_start'], 1.44, places=2)

    def test_price_method(self):
        series = _build_asset_series('TEST', self._cfg(), self._history(), 2020, 2022, 'price')
        self.assertIsNotNone(series)
        last_point = series['points'][-1]
        self.assertAlmostEqual(last_point['value'], 144.0)

    def test_cumulative_method(self):
        series = _build_asset_series('TEST', self._cfg(), self._history(), 2020, 2022, 'cumulative')
        self.assertIsNotNone(series)
        last_pct = series['points'][-1]['value']
        self.assertAlmostEqual(last_pct, 44.0, places=1)

    def test_capital_gains_tax_applied(self):
        series = _build_asset_series(
            'TEST', self._cfg(), self._history(), 2020, 2022, 'cagr',
            apply_capital_gains_tax=True, capital_gains_tax_rate=0.22
        )
        self.assertIsNotNone(series)
        expected = round(1 + (1.44 - 1) * (1 - 0.22), 3)
        self.assertAlmostEqual(series['multiple_from_start'], expected, places=2)
        self.assertTrue(series.get('capital_gains_tax_applied'))

    def test_empty_history_returns_none(self):
        series = _build_asset_series('TEST', self._cfg(), [], 2020, 2022, 'cagr')
        self.assertIsNone(series)

    def test_single_point_returns_none(self):
        history = [(datetime(2020, 12, 31), 100.0)]
        series = _build_asset_series('TEST', self._cfg(), history, 2020, 2020, 'cagr')
        self.assertIsNone(series)
