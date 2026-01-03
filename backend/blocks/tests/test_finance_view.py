import json
from unittest import mock

from datetime import datetime

from django.test import TestCase

from blocks.models import FinanceQueryLog, FinanceQueryAsset
from blocks import views


def _mock_price_stream(assets, start_year, end_year):
    yield {'type': 'log', 'message': f"[데이터 수집] {len(assets)}개 자산 모의 수집"}
    price_payload = {
        asset['id']: {
            'history': [],
            'config': {'label': asset['label'], 'ticker': asset.get('ticker', asset['id'])},
            'source': 'mock',
            'calculation_method': asset.get('calculation_method', 'cagr'),
            'metadata': asset.get('metadata') or {}
        }
        for asset in assets
    }
    yield {'type': 'result', 'data': price_payload}


def _mock_calculator_stream(price_map, start_year, end_year, calculation_method, include_dividends=False, include_tax=False):
    yield {'type': 'log', 'message': "[수익률 계산] 모의 계산 시작"}
    mock_series = []
    for asset_id, data in price_map.items():
        mock_series.append({
            'id': asset_id,
            'label': data['config']['label'],
            'calculation_method': calculation_method,
            'points': [
                {'year': start_year, 'value': 1.0},
                {'year': end_year, 'value': 2.0},
            ],
            'annualized_return_pct': 10.0,
            'multiple_from_start': 2.0
        })
    yield {'type': 'result', 'data': {
        'series': mock_series,
        'table': [],
        'summary': 'mock-summary'
    }}


def _mock_analysis_stream(series_list, start_year, end_year, calculation_method, prompt):
    yield {'type': 'log', 'message': "[분석 생성] 모의 요약 생성"}
    summary = f"{start_year}-{end_year} / {calculation_method} / {len(series_list)} assets"
    yield {'type': 'result', 'data': summary}


class FinanceAnalysisViewTests(TestCase):
    maxDiff = None

    @mock.patch('blocks.views.AnalysisAgent.stream', side_effect=_mock_analysis_stream)
    @mock.patch('blocks.views.CalculatorAgent.stream', side_effect=_mock_calculator_stream)
    @mock.patch('blocks.views.PriceRetrieverAgent.stream', side_effect=_mock_price_stream)
    def test_full_pipeline_with_explicit_assets(self, *_mocks):
        url = '/api/finance/historical-returns'
        payload = {
            'prompt': '10년 전에 비트코인과 애플을 비교해줘',
            'quick_requests': [],
            'context_key': 'safe_assets',
            'custom_assets': [
                {'id': 'AAPL', 'label': '애플', 'ticker': 'AAPL', 'category': '미국 주식'}
            ],
            'calculation_method': 'cagr',
            'include_dividends': False
        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertIn('assets', data['analysis_summary'])
        self.assertEqual(data['calculation_method'], 'cagr')
        self.assertIn('tax_variants', data)
        self.assertIn('tax_on', data['tax_variants'])
        self.assertIn('tax_off', data['tax_variants'])
        requested_labels = [asset['label'] for asset in data['requested_assets']]
        self.assertIn('비트코인', requested_labels)
        self.assertTrue(any('애플' in label for label in requested_labels))
        self.assertEqual(FinanceQueryLog.objects.count(), 1)
        log = FinanceQueryLog.objects.latest('id')
        self.assertEqual(log.assets_count, 2)
        logged_assets = list(log.asset_rows.all())
        labels = [asset.label for asset in logged_assets]
        self.assertTrue(any('비트코인' in label for label in labels))
        self.assertTrue(any('애플' in label for label in labels))
        self.assertEqual(FinanceQueryAsset.objects.count(), 2)

    @mock.patch('blocks.views.PriceRetrieverAgent.stream', side_effect=_mock_price_stream)
    @mock.patch('blocks.views.CalculatorAgent.stream', side_effect=_mock_calculator_stream)
    @mock.patch('blocks.views.AnalysisAgent.stream', side_effect=_mock_analysis_stream)
    def test_streaming_endpoint_yields_result(self, *_mocks):
        url = '/api/finance/historical-returns?stream=1'
        payload = {
            'prompt': '',
            'custom_assets': [{'id': 'bitcoin', 'label': '비트코인', 'ticker': 'BTC-USD'}],
            'calculation_method': 'price'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        body = b''.join(response.streaming_content).decode('utf-8')
        self.assertIn('analysis_summary', body)

    def test_admin_logs_endpoint_includes_assets(self):
        log = FinanceQueryLog.objects.create(
            user_identifier='127.0.0.1',
            context_key='test',
            success=True,
            assets_count=1,
            processing_time_ms=123,
        )
        FinanceQueryAsset.objects.create(
            log=log,
            asset_id='bitcoin',
            label='비트코인',
            ticker='BTC-USD',
            category='디지털 자산',
        )
        response = self.client.get('/api/finance/admin/logs', {'username': 'admin'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertEqual(len(data['logs']), 1)
        self.assertEqual(data['logs'][0]['assets'][0]['label'], '비트코인')

    def test_dividend_reinvestment_affects_returns(self):
        agent = views.CalculatorAgent()
        price_data_map = {
            'JEPI': {
                'history': [
                    (datetime(2020, 12, 31), 50.0),
                    (datetime(2021, 12, 31), 50.0),
                    (datetime(2022, 12, 31), 50.0),
                    (datetime(2023, 12, 31), 50.0),
                ],
                'config': {'id': 'JEPI', 'label': 'JEPI', 'ticker': 'JEPI', 'unit': 'USD', 'category': 'ETF'},
                'source': 'Yahoo Finance',
                'calculation_method': 'cagr',
                'metadata': {
                    'yearly_dividends': {
                        2020: 2.0,
                        2021: 4.0,
                        2022: 4.2,
                        2023: 4.3,
                    },
                    'dividend_unit': 'USD'
                }
            }
        }
        series, _, _, _ = agent.run(price_data_map, 2020, 2023, calculation_method='cagr', include_dividends=True)
        self.assertTrue(series)
        je_series = series[0]
        self.assertGreater(je_series['multiple_from_start'], 1.0)
        self.assertTrue(je_series.get('dividends_reinvested'))

    def test_dividend_reinvestment_not_applied_twice(self):
        agent = views.CalculatorAgent()
        price_data_map = {
            'T': {
                'history': [
                    (datetime(2016, 12, 31), 100.0),
                    (datetime(2017, 12, 31), 110.0),
                    (datetime(2018, 12, 31), 120.0),
                ],
                'config': {
                    'id': 'T',
                    'label': 'AT&T',
                    'ticker': 'T',
                    'unit': 'USD',
                    'category': '미국 주식',
                },
                'source': 'MockSource',
                'calculation_method': 'cagr',
                'metadata': {
                    # Metadata still contains yearly dividends for table display...
                    'yearly_dividends': {
                        2016: 4.0,
                        2017: 4.0,
                    },
                    # ...but indicates the prices already include dividend reinvestment.
                    'dividends_reinvested': True,
                }
            }
        }
        series, _, _, _ = agent.run(price_data_map, 2016, 2018, calculation_method='cagr', include_dividends=True)
        self.assertEqual(len(series), 1)
        att_series = series[0]
        # Without double-application the final multiple should remain the raw price ratio (120/100)
        self.assertAlmostEqual(att_series['multiple_from_start'], 1.2, places=5)
        self.assertTrue(att_series.get('dividends_reinvested'))

    def test_capital_gains_tax_only_applied_when_dividends_and_tax_enabled(self):
        agent = views.CalculatorAgent()
        price_data_map = {
            'US_STOCK': {
                'history': [
                    (datetime(2019, 12, 31), 100.0),
                    (datetime(2020, 12, 31), 120.0),
                    (datetime(2021, 12, 31), 160.0),
                ],
                'config': {
                    'id': 'US_STOCK',
                    'label': '미국 주식',
                    'ticker': 'SPY',
                    'unit': 'USD',
                    'category': '미국 주식',
                },
                'source': 'Yahoo Finance',
                'calculation_method': 'cagr',
                'metadata': {}
            }
        }

        # Baseline: dividends on, tax off -> no capital gains tax adjustment
        series_no_tax, _, _, _ = agent.run(price_data_map, 2019, 2021, calculation_method='cagr', include_dividends=True, include_tax=False)
        self.assertEqual(len(series_no_tax), 1)
        baseline_multiple = series_no_tax[0]['multiple_from_start']
        self.assertAlmostEqual(baseline_multiple, 1.6, places=5)

        # Both toggles on -> capital gains tax of 22% applied on gains above principal
        series_with_tax, _, _, _ = agent.run(price_data_map, 2019, 2021, calculation_method='cagr', include_dividends=True, include_tax=True)
        self.assertEqual(len(series_with_tax), 1)
        after_tax_multiple = series_with_tax[0]['multiple_from_start']
        expected_after_tax = 1 + (0.6 * (1 - 0.22))
        self.assertAlmostEqual(after_tax_multiple, expected_after_tax, places=5)

        # Tax on but dividends toggle off -> capital gains tax should not be applied
        series_tax_without_div, _, _, _ = agent.run(price_data_map, 2019, 2021, calculation_method='cagr', include_dividends=False, include_tax=True)
        self.assertEqual(len(series_tax_without_div), 1)
        self.assertAlmostEqual(series_tax_without_div[0]['multiple_from_start'], baseline_multiple, places=5)

    @mock.patch('blocks.views._enrich_metadata_with_dividend_info', side_effect=lambda cfg, meta: meta)
    @mock.patch('blocks.views._build_yearly_dividend_map', return_value={})
    @mock.patch('blocks.views._fetch_asset_history', return_value=([(datetime(2020, 12, 31), 100.0), (datetime(2021, 12, 31), 120.0)], 'MockSource'))
    @mock.patch('blocks.views.CalculatorAgent.run')
    def test_add_single_asset_returns_tax_variants(self, mock_calc_run, *_mocks):
        def _fake_run(price_map, start_year, end_year, method, include_dividends=False, include_tax=False):
            suffix = 'tax_on' if include_tax else 'tax_off'
            series = [{
                'id': 'AAPL',
                'label': f'AAPL ({suffix})',
                'points': [{'year': start_year, 'value': 0.0}, {'year': end_year, 'value': 1.0}],
                'annualized_return_pct': 12.0 if include_tax else 14.0,
                'multiple_from_start': 1.2 if include_tax else 1.4,
                'calculation_method': method
            }]
            table = [{
                'id': 'AAPL',
                'label': f'AAPL ({suffix})',
                'unit': 'USD',
                'source': 'MockSource',
                'values': [{'year': start_year, 'value': 100.0}]
            }]
            summary = f'summary-{suffix}'
            return series, table, summary, []

        mock_calc_run.side_effect = _fake_run

        payload = {
            'asset_id': 'AAPL',
            'start_year': 2020,
            'end_year': 2021,
            'calculation_method': 'cagr',
            'include_dividends': True,
            'include_tax': True
        }
        response = self.client.post(
            '/api/finance/add-single-asset',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertIn('tax_variants', data)
        self.assertIn('tax_on', data['tax_variants'])
        self.assertIn('tax_off', data['tax_variants'])
        self.assertEqual(data['series']['label'], 'AAPL (tax_on)')
        tax_on_variant = data['tax_variants']['tax_on']
        tax_off_variant = data['tax_variants']['tax_off']
        self.assertEqual(len(tax_on_variant['series']), 1)
        self.assertEqual(len(tax_off_variant['series']), 1)
        self.assertEqual(tax_off_variant['series'][0]['label'], 'AAPL (tax_off)')
        self.assertTrue(tax_on_variant['chart_data_table'])
