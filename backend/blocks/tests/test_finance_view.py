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


def _mock_calculator_stream(price_map, start_year, end_year, calculation_method, include_dividends=False):
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
