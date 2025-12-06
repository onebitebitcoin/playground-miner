"""
Tests for AnalysisAgent color coding and deterministic comparison list generation.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Setup Django environment
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRENT_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground_server.settings')

# Use workspace-local directory for bitcoinlib artifacts
local_bitcoinlib_dir = os.path.join(CURRENT_DIR, '.bitcoinlib')
os.environ.setdefault('BCL_DATA_DIR', local_bitcoinlib_dir)
os.makedirs(local_bitcoinlib_dir, exist_ok=True)

import django
django.setup()

from blocks.views import AnalysisAgent


class AnalysisAgentColorCodingTests(unittest.TestCase):
    """Verify that AnalysisAgent always applies correct BTC-relative colors."""

    def setUp(self):
        self.agent = AnalysisAgent()
        self.bitcoin = {
            'label': '비트코인',
            'annualized_return_pct': 82.3,
            'multiple_from_start': 15.0,
        }
        self.bitcoin['annualized_cagr_pct'] = self.bitcoin['annualized_return_pct']
        self.other_assets = [
            {
                'label': '테크주 A',
                'annualized_return_pct': 120.0,
                'multiple_from_start': 25.0,
            },
            {
                'label': '안전자산 B',
                'annualized_return_pct': 12.0,
                'multiple_from_start': 2.0,
            },
        ]
        for asset in self.other_assets:
            asset['annualized_cagr_pct'] = asset['annualized_return_pct']

    @patch('blocks.views.requests.post')
    def test_ai_analysis_returns_bitcoin_focus_block_only(self, mock_post):
        """AI 경로도 비트코인 하이라이트 블록만 반환해야 한다."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': "<p>AI 요약</p><ul><li>잘못된 LLM 리스트</li></ul>"
                }
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        html = self.agent._generate_ai_analysis(
            self.bitcoin,
            self.other_assets,
            2015,
            2024,
            'cagr',
            '테스트 요청 100만원 투자',
        )

        self.assertNotIn("대표 자산 성과", html)
        self.assertNotIn("대표 주식 성과", html)
        self.assertIn("비트코인", html)

    def test_investment_amount_detected_and_rendered(self):
        """Investment amounts in prompt should appear in the Bitcoin summary block."""
        info = self.agent._extract_investment_amount("비트코인에 100만원을 투자했다면?")
        self.assertIsNotNone(info)
        block = self.agent._build_bitcoin_focus_block(
            self.bitcoin,
            2015,
            2024,
            "연평균 상승률",
            investment_info=info,
        )
        self.assertIn("100만원", block)
        self.assertIn("투자했다면", block)
        self.assertIn("1,500만 원", block)
        self.assertNotIn("대표 자산 성과", block)

    def test_fallback_analysis_focuses_on_bitcoin_only(self):
        """Fallback 분석에서도 비교 섹션 텍스트가 없어야 한다."""
        html = self.agent._generate_fallback_analysis(
            self.bitcoin,
            self.other_assets,
            2015,
            2024,
            'cagr',
            prompt="100만원을 투자했다면?",
        )
        self.assertNotIn("대표 자산 성과", html)
        self.assertNotIn("대표 주식 성과", html)
        self.assertIn("비트코인", html)

    def test_bitcoin_focus_includes_cagr_even_for_price_mode(self):
        """Analysis summary should still mention Bitcoin CAGR in non-CAGR modes."""
        block = self.agent._build_bitcoin_focus_block(
            self.bitcoin,
            2015,
            2024,
            "가격 상승률",
            investment_info=None,
        )
        self.assertIn("연평균 상승률", block)
        self.assertIn("bg-yellow-200 text-yellow-900 px-4 py-1 rounded font-black text-3xl", block)
        self.assertNotIn("대표 자산 성과", block)


if __name__ == "__main__":
    unittest.main()
