import json
from unittest import mock

from django.db import OperationalError
from django.test import RequestFactory, TestCase

from blocks import views


class CompatibilityAgentCacheViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_list_view_handles_missing_table(self):
        request = self.factory.get('/api/compatibility/admin/cache', {'username': 'admin'})
        with mock.patch('blocks.views.CompatibilityAgentCache.objects') as mock_manager:
            mock_manager.all.side_effect = OperationalError('no such table')
            response = views.compatibility_agent_cache_list_view(request)

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertFalse(payload['ok'])
        self.assertEqual(payload['caches'], [])
        self.assertIn('캐시', payload['error'])
