
import os
import django
from django.conf import settings

if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground_server.settings')
    django.setup()

import unittest
from blocks.views import CalculatorAgent

class TestPriceDisplay(unittest.TestCase):
    def test_chart_data_table_structure(self):
        agent = CalculatorAgent()
        
        # Mock price data
        price_data_map = {
            'bitcoin': {
                'history': [
                    # datetime object needed? views.py uses dt.year
                    # Need to mock datetime objects or ensure _build_asset_series handles tuples
                    # _build_asset_series expects (dt, value) where dt has .year
                ],
                'config': {
                    'id': 'bitcoin',
                    'label': 'Bitcoin',
                    'unit': 'USD',
                    'category': 'Crypto'
                },
                'source': 'test',
                'calculation_method': 'price'
            }
        }
        
        # Since _build_asset_series logic is complex with datetime, 
        # I will verify _build_chart_data_table logic directly by passing a mock series_list
        
        series_list = [
            {
                'id': 'bitcoin',
                'label': 'Bitcoin',
                'unit': 'USD',
                'source': 'test',
                'points': [
                    {'year': 2024, 'value': 90000.0, 'raw_value': 90000.0, 'multiple': 1.5},
                    {'year': 2025, 'value': 95000.0, 'raw_value': 95000.0, 'multiple': 1.6},
                ]
            }
        ]
        
        table_data = agent._build_chart_data_table(series_list, 'price')
        
        print("\nTable Data:", table_data)
        
        entry = table_data[0]
        self.assertEqual(entry['id'], 'bitcoin')
        self.assertEqual(entry['value_label'], '가격')
        
        # Check keys
        self.assertIn('values', entry)
        self.assertEqual(entry['values'][0]['value'], 90000.0) # Should use raw_value

if __name__ == '__main__':
    unittest.main()
