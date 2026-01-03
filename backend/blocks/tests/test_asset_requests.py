from django.test import SimpleTestCase

from blocks import views


class AssetSanitizationTests(SimpleTestCase):
    def test_sanitizes_string_entries(self):
        raw = ['  AAPL  ', '삼성전자']
        sanitized = views._sanitize_custom_assets(raw)
        self.assertEqual(len(sanitized), 2)
        self.assertEqual(sanitized[0]['id'], 'AAPL')
        self.assertEqual(sanitized[1]['label'], '삼성전자')

    def test_preserves_synthetic_metadata(self):
        raw = [{
            'id': 'syn-market',
            'label': '예금 3.5%',
            'ticker': 'SYNTH-DEPOSIT-0350',
            'synthetic_asset': 'deposit',
            'target_rate_pct': 3.5,
            'category': '예적금',
            'unit': '%'
        }]
        sanitized = views._sanitize_custom_assets(raw)
        asset = sanitized[0]
        self.assertEqual(asset['synthetic_asset'], 'deposit')
        self.assertEqual(asset['target_rate_pct'], 3.5)
        self.assertEqual(asset['category'], '예적금')


class AssetRequestBuilderTests(SimpleTestCase):
    def test_injects_bitcoin_when_missing(self):
        entries = [{'id': 'AAPL', 'label': '애플', 'ticker': 'AAPL'}]
        assets = views._build_requested_assets(entries, 'cagr')
        labels = [asset['label'] for asset in assets]
        self.assertIn('비트코인', labels)
        self.assertTrue(labels.index('비트코인') == 0, "Bitcoin should be inserted first when missing")

    def test_deduplicates_equivalent_assets(self):
        entries = [
            {'id': 'bitcoin', 'label': '비트코인', 'ticker': 'BTC-USD'},
            {'id': 'BTC-USD', 'label': 'Bitcoin', 'ticker': 'BTC-USD'},
            {'id': 'bitcoin', 'label': '비트코인', 'ticker': 'BTC-USD'},
        ]
        assets = views._build_requested_assets(entries, 'cagr')
        btc_assets = [asset for asset in assets if views._asset_entry_is_bitcoin(asset)]
        self.assertEqual(len(btc_assets), 1)

    def test_preserves_synthetic_assets(self):
        entries = [{
            'id': 'SYNTH-DEPOSIT-0300',
            'label': '예금 3%',
            'ticker': 'SYNTH-DEPOSIT-0300',
            'synthetic_asset': 'deposit',
            'target_rate_pct': 3.0
        }]
        assets = views._build_requested_assets(entries, 'cagr')
        self.assertEqual(len(assets), 2)  # deposit + bitcoin
        deposit = next(asset for asset in assets if asset['id'] != 'bitcoin')
        self.assertEqual(deposit['metadata']['synthetic_asset'], 'deposit')
        self.assertEqual(deposit['metadata']['target_rate_pct'], 3.0)
