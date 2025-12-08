from django.urls import path, re_path
from . import views

urlpatterns = [
    path('status', views.status_view, name='status'),
    path('blocks', views.blocks_view, name='blocks'),
    path('mine', views.mine_view, name='mine'),
    path('stream', views.stream_view, name='stream'),
    path('finance/historical-returns', views.finance_historical_returns_view, name='finance_historical_returns'),
    path('finance/yearly-closing-prices', views.finance_yearly_closing_prices_view, name='finance_yearly_closing_prices'),
    path('finance/custom-asset/resolve', views.finance_resolve_custom_asset_view, name='finance_resolve_custom_asset'),
    path('finance/quick-requests', views.finance_quick_requests_view, name='finance_quick_requests'),
    path('finance/quick-compare-groups', views.finance_quick_compare_groups_view, name='finance_quick_compare_groups'),
    path('finance/price-cache', views.finance_price_cache_view, name='finance_price_cache'),
    # Accept both with/without trailing slash
    re_path(r'^register_nick/?$', views.register_nick_view, name='register_nick'),
    re_path(r'^check_nick/?$', views.check_nick_view, name='check_nick'),
    re_path(r'^init_reset/?$', views.init_reset_view, name='init_reset'),
    # Mnemonic endpoints
    path('mnemonic/request', views.request_mnemonic_view, name='request_mnemonic'),
    path('mnemonic/generate', views.generate_mnemonic_view, name='generate_mnemonic'),
    path('mnemonic/save', views.save_mnemonic_view, name='save_mnemonic'),
    path('mnemonic/admin', views.admin_mnemonics_view, name='admin_mnemonics'),
    path('mnemonic/balance', views.mnemonic_balance_view, name='mnemonic_balance'),
    path('mnemonic/admin/balance', views.admin_set_mnemonic_balance_view, name='admin_mnemonic_balance'),
    path('mnemonic/balance/onchain', views.mnemonic_onchain_balance_view, name='mnemonic_onchain_balance'),
    path('mnemonic/admin/delete', views.admin_delete_mnemonic_view, name='admin_delete_mnemonic'),
    path('mnemonic/admin/xpub', views.admin_mnemonic_xpub_view, name='admin_mnemonic_xpub'),
    path('mnemonic/admin/address', views.admin_mnemonic_address_view, name='admin_mnemonic_address'),
    path('mnemonic/admin/unassign', views.admin_unassign_mnemonic_view, name='admin_mnemonic_unassign'),
    path('mnemonic/validate', views.validate_mnemonic_view, name='validate_mnemonic'),
    # Exchange rate endpoints
    path('exchange-rates', views.exchange_rates_view, name='exchange_rates'),
    path('exchange-rates/admin', views.admin_exchange_rates_view, name='admin_exchange_rates'),
    # Withdrawal fee endpoints
    path('withdrawal-fees', views.withdrawal_fees_view, name='withdrawal_fees'),
    path('withdrawal-fees/admin', views.admin_withdrawal_fees_view, name='admin_withdrawal_fees'),
    # Lightning service endpoints
    path('lightning-services', views.lightning_services_view, name='lightning_services'),
    path('lightning-services/admin', views.admin_lightning_services_view, name='admin_lightning_services'),
    # New routing system endpoints
    path('service-nodes/admin', views.admin_service_nodes_view, name='admin_service_nodes'),
    path('routes/admin', views.admin_routes_view, name='admin_routes'),
    path('optimal-paths', views.get_optimal_paths_view, name='optimal_paths'),
    path('routing-snapshot', views.routing_snapshot_view, name='routing_snapshot'),
    # Sidebar config endpoints
    path('sidebar-config', views.sidebar_config_view, name='sidebar_config'),
    path('sidebar-config/admin', views.admin_update_sidebar_config_view, name='admin_sidebar_config'),
    # Kingstone wallet endpoints
    path('kingstone/wallets', views.kingstone_wallets_view, name='kingstone_wallets'),
    path('kingstone/pin/verify', views.kingstone_verify_pin_view, name='kingstone_verify_pin'),
    path('kingstone/pin/register', views.kingstone_register_pin_view, name='kingstone_register_pin'),
    path('kingstone/wallet/delete', views.kingstone_delete_wallet_view, name='kingstone_delete_wallet'),
    path('kingstone/wallet/address', views.kingstone_wallet_address_view, name='kingstone_wallet_address'),
    path('kingstone/admin/wallets', views.admin_kingstone_wallets_view, name='admin_kingstone_wallets'),
    # Wallet password
    path('wallet/password/admin', views.admin_set_wallet_password_view, name='admin_set_wallet_password'),
    path('wallet/password/check', views.wallet_password_check_view, name='wallet_password_check'),
    path('wallet/password/admin/get', views.admin_get_wallet_password_view, name='admin_get_wallet_password'),
    # Finance management endpoints
    path('finance/admin/logs', views.admin_finance_logs_view, name='admin_finance_logs'),
    path('finance/admin/stats', views.admin_finance_stats_view, name='admin_finance_stats'),
    # Agent prompt management endpoints
    path('finance/admin/agent-prompts', views.admin_agent_prompts_view, name='admin_agent_prompts'),
    path('finance/admin/agent-prompts/<str:agent_type>', views.admin_agent_prompt_detail_view, name='admin_agent_prompt_detail'),
    path('finance/admin/quick-requests', views.admin_finance_quick_requests_view, name='admin_finance_quick_requests'),
    path('finance/admin/quick-requests/<int:pk>', views.admin_finance_quick_request_detail_view, name='admin_finance_quick_request_detail'),
    path('finance/admin/quick-compare-groups', views.admin_finance_quick_compare_groups_view, name='admin_finance_quick_compare_groups'),
    path('finance/admin/quick-compare-groups/<int:pk>', views.admin_finance_quick_compare_group_detail_view, name='admin_finance_quick_compare_group_detail'),
    path('finance/admin/price-cache', views.admin_price_cache_view, name='admin_price_cache'),
    path('finance/admin/price-cache/<int:pk>', views.admin_price_cache_detail_view, name='admin_price_cache_detail'),
]
