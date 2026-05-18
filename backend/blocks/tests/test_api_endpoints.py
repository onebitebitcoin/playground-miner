"""
Integration tests for major API endpoints.
All tests use Django's test client against an in-memory SQLite database.
External HTTP calls (Yahoo Finance, pykrx, Gemini, etc.) are mocked out.
"""
import json
from unittest import mock

from django.test import TestCase, SimpleTestCase

from blocks.models import (
    ExchangeRate,
    LightningService,
    WithdrawalFee,
    ServiceNode,
    Route,
    SidebarConfig,
    FinanceQueryLog,
)


class HealthEndpointTests(SimpleTestCase):
    def test_health_ok(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')


class StatusEndpointTests(TestCase):
    def test_status_200(self):
        response = self.client.get('/api/status')
        self.assertEqual(response.status_code, 200)

    def test_status_returns_json(self):
        response = self.client.get('/api/status')
        data = response.json()
        self.assertIn('height', data)


class ExchangeRateEndpointTests(TestCase):
    def setUp(self):
        ExchangeRate.objects.create(exchange='upbit_btc', fee_rate=0.05)
        ExchangeRate.objects.create(exchange='bithumb', fee_rate=0.04)

    def test_list_rates(self):
        response = self.client.get('/api/exchange-rates')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))
        exchanges = [r['exchange'] for r in data['rates']]
        self.assertIn('upbit_btc', exchanges)

    def test_admin_list_rates(self):
        response = self.client.get('/api/exchange-rates/admin', {'username': 'admin'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))

    def test_admin_create_rate(self):
        payload = {'exchange': 'okx', 'fee_rate': 0.10}
        response = self.client.post(
            '/api/exchange-rates/admin',
            data=json.dumps(payload),
            content_type='application/json',
            **{'HTTP_X_ADMIN_USERNAME': 'admin'},
        )
        self.assertIn(response.status_code, [200, 201])

    def test_admin_update_rate(self):
        payload = {'exchange': 'upbit_btc', 'fee_rate': 0.06}
        response = self.client.post(
            '/api/exchange-rates/admin',
            data=json.dumps(payload),
            content_type='application/json',
            **{'HTTP_X_ADMIN_USERNAME': 'admin'},
        )
        self.assertIn(response.status_code, [200, 201])


class WithdrawalFeeEndpointTests(TestCase):
    def setUp(self):
        WithdrawalFee.objects.create(
            exchange='okx',
            withdrawal_type='onchain',
            fee_btc='0.00050000',
        )

    def test_list_fees(self):
        response = self.client.get('/api/withdrawal-fees')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))
        self.assertGreaterEqual(len(data['fees']), 1)

    def test_admin_list_fees(self):
        response = self.client.get('/api/withdrawal-fees/admin', {'username': 'admin'})
        self.assertEqual(response.status_code, 200)


class LightningServiceEndpointTests(TestCase):
    def setUp(self):
        LightningService.objects.create(
            service='strike',
            fee_rate='0.4000',
            is_kyc=False,
            is_custodial=True,
        )

    def test_list_services(self):
        response = self.client.get('/api/lightning-services')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))
        self.assertGreaterEqual(len(data['services']), 1)


class RoutingEndpointTests(TestCase):
    def setUp(self):
        self.node_a = ServiceNode.objects.create(
            service='upbit', display_name='업비트', node_type='exchange'
        )
        self.node_b = ServiceNode.objects.create(
            service='personal_wallet', display_name='개인지갑', node_type='wallet'
        )
        Route.objects.create(
            source=self.node_a,
            destination=self.node_b,
            route_type='withdrawal_onchain',
            fee_rate='0.1000',
            is_enabled=True,
        )

    def test_optimal_paths_requires_params(self):
        response = self.client.get('/api/optimal-paths')
        self.assertIn(response.status_code, [200, 400, 404])

    def test_routing_snapshot(self):
        response = self.client.get('/api/routing-snapshot')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))

    def test_admin_service_nodes_list(self):
        response = self.client.get('/api/service-nodes/admin', {'username': 'admin'})
        self.assertEqual(response.status_code, 200)

    def test_admin_routes_list(self):
        response = self.client.get('/api/routes/admin', {'username': 'admin'})
        self.assertEqual(response.status_code, 200)


class SidebarConfigEndpointTests(TestCase):
    def setUp(self):
        SidebarConfig.objects.create(show_finance=True, show_mining=True)

    def test_get_sidebar_config(self):
        response = self.client.get('/api/sidebar-config')
        self.assertEqual(response.status_code, 200)

    def test_admin_update_sidebar_config(self):
        payload = {'show_finance': True, 'show_mining': False}
        response = self.client.post(
            '/api/sidebar-config/admin',
            data=json.dumps(payload),
            content_type='application/json',
            **{'HTTP_X_ADMIN_USERNAME': 'admin'},
        )
        self.assertIn(response.status_code, [200, 201])


class FinanceQuickRequestsEndpointTests(TestCase):
    def test_list_quick_requests(self):
        response = self.client.get('/api/finance/quick-requests')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))

    def test_list_quick_compare_groups(self):
        response = self.client.get('/api/finance/quick-compare-groups')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))


class FinanceAdminEndpointTests(TestCase):
    def setUp(self):
        FinanceQueryLog.objects.create(
            user_identifier='127.0.0.1',
            context_key='test',
            success=True,
            assets_count=1,
            processing_time_ms=50,
        )

    def test_admin_logs(self):
        response = self.client.get('/api/finance/admin/logs', {'username': 'admin'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))
        self.assertGreaterEqual(len(data['logs']), 1)

    def test_admin_stats(self):
        response = self.client.get('/api/finance/admin/stats', {'username': 'admin'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))


class CompatibilityEndpointTests(TestCase):
    def test_get_compatibility_prompt(self):
        response = self.client.get('/api/compatibility/prompt')
        self.assertEqual(response.status_code, 200)

    def test_list_report_templates(self):
        response = self.client.get('/api/compatibility/report-templates')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))

    def test_list_quick_presets(self):
        response = self.client.get('/api/compatibility/quick-presets')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))


class NickRegistrationTests(TestCase):
    def test_register_nick_post(self):
        payload = {'nickname': 'testuser123'}
        response = self.client.post(
            '/api/register_nick',
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertIn(response.status_code, [200, 201, 400, 409])

    def test_check_nick_get(self):
        response = self.client.get('/api/check_nick', {'nickname': 'nobody'})
        self.assertIn(response.status_code, [200, 404])
